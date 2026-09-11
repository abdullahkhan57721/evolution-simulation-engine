import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: disclosure
    property var theme
    property string title: "Details"
    property alias contentItem: body.data
    property bool expanded: false
    spacing: theme ? theme.space2 : 10

    Button {
        id: toggle
        Layout.fillWidth: true
        implicitHeight: 36
        leftPadding: 4
        rightPadding: 4
        activeFocusOnTab: true
        Accessible.name: disclosure.title
        Accessible.role: Accessible.Button
        Accessible.description: disclosure.expanded ? "Expanded." : "Collapsed."
        onClicked: disclosure.expanded = !disclosure.expanded
        contentItem: RowLayout {
            Label {
                text: disclosure.expanded ? "▾" : "▸"
                color: disclosure.theme ? disclosure.theme.accent : "#55b8ff"
            }
            Label {
                text: disclosure.title
                color: disclosure.theme ? disclosure.theme.text : "#edf3fb"
                font.weight: Font.DemiBold
                Layout.fillWidth: true
            }
        }
        background: Rectangle {
            color: toggle.activeFocus
                ? (disclosure.theme ? disclosure.theme.surfaceRaised : "#1c2940")
                : "transparent"
            radius: disclosure.theme ? disclosure.theme.radiusSmall : 7
            border.width: toggle.activeFocus ? 2 : 0
            border.color: disclosure.theme ? disclosure.theme.focus : "#ffffff"
        }
    }

    ColumnLayout {
        id: body
        visible: disclosure.expanded
        Layout.fillWidth: true
        spacing: disclosure.theme ? disclosure.theme.space2 : 10
    }
}
