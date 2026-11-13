import Foundation
import Darwin

/// Whole-machine CPU and memory use, read from the kernel once per sample.
final class SystemMonitor {
    struct Sample {
        /// Share of CPU time spent busy since the previous sample, 0 to 100. Nil until there is a baseline.
        let cpu: Double?
        /// Share of physical memory in use, 0 to 100.
        let memory: Double?
    }

    var onSample: ((Sample) -> Void)?
    private var timer: Timer?
    private var previousTicks: [CoreTicks] = []
    private let physicalMemory = ProcessInfo.processInfo.physicalMemory

    private struct CoreTicks {
        let busy: UInt32
        let total: UInt32
    }

    func start(interval: TimeInterval = 1) {
        sample()
        let timer = Timer(timeInterval: interval, repeats: true) { [weak self] _ in self?.sample() }
        RunLoop.main.add(timer, forMode: .common)
        self.timer = timer
    }

    func stop() {
        timer?.invalidate()
        timer = nil
    }

    private func sample() {
        onSample?(Sample(cpu: cpuPercent(), memory: memoryPercent()))
    }

    /// The kernel's tick counters are 32-bit and wrap, so every delta uses wrapping subtraction.
    private func cpuPercent() -> Double? {
        var info: processor_info_array_t?
        var coreCount: natural_t = 0
        var infoCount: mach_msg_type_number_t = 0
        guard host_processor_info(mach_host_self(), PROCESSOR_CPU_LOAD_INFO, &coreCount, &info, &infoCount) == KERN_SUCCESS,
              let info else { return nil }
        defer {
            vm_deallocate(mach_task_self_, vm_address_t(UInt(bitPattern: info)),
                          vm_size_t(infoCount) * vm_size_t(MemoryLayout<integer_t>.stride))
        }

        let states = Int(CPU_STATE_MAX)
        let ticks: [CoreTicks] = (0..<Int(coreCount)).map { core in
            let base = core * states
            let user = UInt32(bitPattern: info[base + Int(CPU_STATE_USER)])
            let system = UInt32(bitPattern: info[base + Int(CPU_STATE_SYSTEM)])
            let nice = UInt32(bitPattern: info[base + Int(CPU_STATE_NICE)])
            let idle = UInt32(bitPattern: info[base + Int(CPU_STATE_IDLE)])
            let busy = user &+ system &+ nice
            return CoreTicks(busy: busy, total: busy &+ idle)
        }
        defer { previousTicks = ticks }

        guard previousTicks.count == ticks.count else { return nil }
        var busy: UInt64 = 0
        var total: UInt64 = 0
        for (now, before) in zip(ticks, previousTicks) {
            busy += UInt64(now.busy &- before.busy)
            total += UInt64(now.total &- before.total)
        }
        guard total > 0 else { return nil }
        return Double(busy) / Double(total) * 100
    }

    /// Activity Monitor's "Memory Used": app memory, wired memory and compressed memory.
    private func memoryPercent() -> Double? {
        var stats = vm_statistics64()
        var count = mach_msg_type_number_t(MemoryLayout<vm_statistics64_data_t>.stride / MemoryLayout<integer_t>.stride)
        let result = withUnsafeMutablePointer(to: &stats) { pointer in
            pointer.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
                host_statistics64(mach_host_self(), HOST_VM_INFO64, $0, &count)
            }
        }
        guard result == KERN_SUCCESS, physicalMemory > 0 else { return nil }
        let pages = UInt64(stats.active_count) + UInt64(stats.wire_count) + UInt64(stats.compressor_page_count)
        let used = pages * UInt64(vm_kernel_page_size)
        return min(100, Double(used) / Double(physicalMemory) * 100)
    }
}
