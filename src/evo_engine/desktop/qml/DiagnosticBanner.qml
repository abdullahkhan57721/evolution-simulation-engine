import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: banner
    property var theme
    property string tone: "neutral"
    property string title: ""
    property string message: ""
    property string remediation: ""

    implicitHeight: content.implicitHeight + 28
    radius: theme ? theme.radiusSmall : 7
    color: tone === "error"
        ? Qt.rgba(1.0, 0.49, 0.55, 0.10)
        : tone === "warning"
            ? Qt.rgba(1.0, 0.78, 0.4, 0.10)
            : Qt.rgba(0.33, 0.72, 1.0, 0.08)
    border.width: 1
    border.color: tone === "error"
        ? (theme ? theme.danger : "#ff7d8c")
        : tone === "warning"
            ? (theme ? theme.warning : "#ffc766")
            : (theme ? theme.border : "#2a3a55")

    ColumnLayout {
        id: content
        anchors.fill: parent
        anchors.margins: 14
        spacing: 5
        Label {
            visible: banner.title.length > 0
            text: banner.title
            color: banner.theme ? banner.theme.text : "#edf3fb"
            font.weight: Font.DemiBold
            font.pixelSize: banner.theme ? banner.theme.textBody : 14
        }
        Label {
            text: banner.message
            color: banner.theme ? banner.theme.mutedText : "#9fb0c7"
            wrapMode: Text.Wrap
            Layout.fillWidth: true
        }
        Label {
            visible: banner.remediation.length > 0
            text: banner.remediation
            color: banner.theme ? banner.theme.subtleText : "#71839d"
            wrapMode: Text.Wrap
            Layout.fillWidth: true
            font.pixelSize: banner.theme ? banner.theme.textSmall : 12
        }
    }
}
