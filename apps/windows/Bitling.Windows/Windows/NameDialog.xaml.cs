using System.Windows;

namespace Bitling.Windows;

/// Native name prompt, ported from AppDelegate.askName in main.swift, which used an
/// NSAlert with an accessory text field for both the first-hatch naming and rename.
public partial class NameDialog : Window
{
    public string? Result { get; private set; }
    private readonly bool _first;
    private readonly string _suggestion;

    public NameDialog(bool first, string suggestion)
    {
        InitializeComponent();
        _first = first;
        _suggestion = suggestion;
        Headline.Text = first ? "It booted up!" : "Rename your Bitling";
        Body.Text = first
            ? "Give your Bitling a name. You can change it later from the tray menu."
            : "Pick a new name.";
        NameBox.Text = suggestion;
        OkButton.Content = first ? "Name it" : "Rename";
        Loaded += (_, _) => { NameBox.Focus(); NameBox.SelectAll(); };
    }

    private void OnOk(object sender, RoutedEventArgs e)
    {
        var typed = NameBox.Text.Trim();
        Result = typed.Length > 0 ? typed : (_first ? _suggestion : null);
        DialogResult = true;
    }

    private void OnCancel(object sender, RoutedEventArgs e)
    {
        Result = _first ? _suggestion : null;
        DialogResult = false;
    }
}
