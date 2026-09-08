import QtQuick
import QtQuick.Controls

Rectangle {
    id: badge
    property var theme
    property string text: ""
    property string tone: "neutral"

    implicitWidth: label.implicitWidth + 20
    implicitHeight: 26
    radius: height / 2
    color: tone === "success"
        ? Qt.rgba(0.33, 0.84, 0.62, 0.15)
        : tone === "warning"
            ? Qt.rgba(1.0, 0.78, 0.4, 0.15)
            : tone === "error"
                ? Qt.rgba(1.0, 0.49, 0.55, 0.15)
                : (theme ? theme.canvasRaised : "#111a2b")
    border.width: 1
    border.color: tone === "success"
        ? (theme ? theme.success : "#55d69e")
        : tone === "warning"
            ? (theme ? theme.warning : "#ffc766")
            : tone === "error"
                ? (theme ? theme.danger : "#ff7d8c")
                : (theme ? theme.border : "#2a3a55")

    Label {
        id: label
        anchors.centerIn: parent
        text: badge.text
        color: badge.tone === "success"
            ? (badge.theme ? badge.theme.success : "#55d69e")
            : badge.tone === "warning"
                ? (badge.theme ? badge.theme.warning : "#ffc766")
                : badge.tone === "error"
                    ? (badge.theme ? badge.theme.danger : "#ff7d8c")
                    : (badge.theme ? badge.theme.mutedText : "#9fb0c7")
        font.pixelSize: badge.theme ? badge.theme.textSmall : 12
        font.weight: Font.DemiBold
    }
}
