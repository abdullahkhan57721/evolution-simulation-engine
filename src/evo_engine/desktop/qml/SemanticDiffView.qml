import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

SurfacePanel {
    id: root
    property var theme
    property var diffModel

    implicitHeight: content.implicitHeight + theme.space4 * 2

    ColumnLayout {
        id: content
        anchors.fill: parent
        anchors.margins: theme.space4
        spacing: theme.space3

        RowLayout {
            Layout.fillWidth: true
            Label {
                text: "Changes from parent revision"
                color: theme.text
                font.pixelSize: 17
                font.weight: Font.DemiBold
                Layout.fillWidth: true
            }
            StatusBadge { theme: root.theme; text: "SEMANTIC DIFF"; tone: "neutral" }
        }

        Repeater {
            model: root.diffModel
            delegate: ColumnLayout {
                required property string groupName
                required property string label
                required property string beforeValue
                required property string afterValue
                required property string tone
                Layout.fillWidth: true
                spacing: theme.space1

                Label {
                    text: groupName.toUpperCase() + " · " + label
                    color: tone === "warning" ? theme.warning : theme.subtleText
                    font.pixelSize: theme.textSmall
                    font.weight: Font.DemiBold
                }
                Label {
                    text: beforeValue + "  →  " + afterValue
                    color: theme.mutedText
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }
            }
        }
    }
}
