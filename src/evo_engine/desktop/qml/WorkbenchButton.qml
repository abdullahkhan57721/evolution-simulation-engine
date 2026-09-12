import QtQuick
import QtQuick.Controls

Button {
    id: control
    property var theme
    property bool primary: false
    property bool selected: false

    implicitHeight: 40
    leftPadding: theme ? theme.space3 : 16
    rightPadding: theme ? theme.space3 : 16
    activeFocusOnTab: true

    Accessible.name: text
    Accessible.role: Accessible.Button
    Accessible.checked: selected
    Accessible.description: enabled ? "" : "Unavailable in the current Workbench state."

    contentItem: Label {
        text: control.text
        color: !control.enabled
            ? (control.theme ? control.theme.subtleText : "#71839d")
            : control.primary
                ? (control.theme ? control.theme.accentText : "#04131f")
                : (control.theme ? control.theme.text : "#edf3fb")
        font.pixelSize: control.theme ? control.theme.textBody : 14
        font.weight: Font.DemiBold
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        radius: control.theme ? control.theme.radiusSmall : 7
        color: !control.enabled
            ? (control.theme ? control.theme.canvasRaised : "#111a2b")
            : control.down
                ? (control.primary
                    ? (control.theme ? control.theme.accentStrong : "#249be8")
                    : (control.theme ? control.theme.surfaceRaised : "#1c2940"))
                : control.hovered || control.activeFocus || control.selected
                    ? (control.primary
                        ? (control.theme ? control.theme.accent : "#55b8ff")
                        : (control.theme ? control.theme.surfaceRaised : "#1c2940"))
                    : control.primary
                        ? (control.theme ? control.theme.accent : "#55b8ff")
                        : (control.theme ? control.theme.surface : "#162033")
        border.width: control.activeFocus ? 2 : (control.primary ? 0 : 1)
        border.color: control.activeFocus
            ? (control.theme ? control.theme.focus : "#ffd166")
            : control.selected
                ? (control.theme ? control.theme.accent : "#55b8ff")
                : (control.theme ? control.theme.border : "#2a3a55")
    }
}
