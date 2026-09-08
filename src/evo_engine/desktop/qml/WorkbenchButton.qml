import QtQuick
import QtQuick.Controls

Button {
    id: control
    property var theme
    property bool primary: false

    implicitHeight: 38
    leftPadding: theme ? theme.space3 : 16
    rightPadding: theme ? theme.space3 : 16

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
                : control.hovered
                    ? (control.primary
                        ? (control.theme ? control.theme.accent : "#55b8ff")
                        : (control.theme ? control.theme.surfaceRaised : "#1c2940"))
                    : control.primary
                        ? (control.theme ? control.theme.accent : "#55b8ff")
                        : (control.theme ? control.theme.surface : "#162033")
        border.width: control.primary ? 0 : 1
        border.color: control.theme ? control.theme.border : "#2a3a55"
    }
}
