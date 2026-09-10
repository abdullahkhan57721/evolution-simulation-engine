import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

SurfacePanel {
    id: root
    required property var theme
    required property string title
    required property var model
    implicitHeight: content.implicitHeight + root.theme.space4 * 2

    ColumnLayout {
        id: content
        anchors.fill: parent
        anchors.margins: root.theme.space4
        spacing: root.theme.space2

        Label {
            text: root.title
            color: root.theme.text
            font.pixelSize: 17
            font.weight: Font.DemiBold
        }

        Repeater {
            model: root.model
            delegate: ColumnLayout {
                required property string label
                required property string value
                Layout.fillWidth: true
                spacing: root.theme.space1
                Label {
                    text: label
                    color: root.theme.text
                    font.pixelSize: root.theme.textSmall
                    font.weight: Font.DemiBold
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }
                Label {
                    text: value
                    color: root.theme.mutedText
                    font.pixelSize: root.theme.textSmall
                    wrapMode: Text.WrapAnywhere
                    Layout.fillWidth: true
                }
            }
        }
    }
}
