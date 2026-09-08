import QtQuick
import QtQuick.Controls

Button {
    id: control
    property var theme
    property bool selected: false

    implicitHeight: 42
    leftPadding: theme ? theme.space3 : 16
    rightPadding: theme ? theme.space3 : 16

    contentItem: Label {
        text: control.text
        color: control.selected
            ? (control.theme ? control.theme.text : "#edf3fb")
            : (control.theme ? control.theme.mutedText : "#9fb0c7")
        font.pixelSize: control.theme ? control.theme.textBody : 14
        font.weight: control.selected ? Font.DemiBold : Font.Normal
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        radius: control.theme ? control.theme.radiusSmall : 7
        color: control.selected
            ? Qt.rgba(0.33, 0.72, 1.0, 0.12)
            : control.hovered
                ? (control.theme ? control.theme.surfaceRaised : "#1c2940")
                : "transparent"
        border.width: control.selected ? 1 : 0
        border.color: control.theme ? control.theme.accent : "#55b8ff"
    }
}
