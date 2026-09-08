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
        implicitHeight: 34
        leftPadding: 0
        rightPadding: 0
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
        background: Rectangle { color: "transparent" }
    }

    ColumnLayout {
        id: body
        visible: disclosure.expanded
        Layout.fillWidth: true
        spacing: disclosure.theme ? disclosure.theme.space2 : 10
    }
}
