import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    property var theme
    property string eyebrow: ""
    property string title: ""
    property string description: ""
    spacing: theme ? theme.space1 : 6

    Label {
        visible: parent.eyebrow.length > 0
        text: parent.eyebrow.toUpperCase()
        color: parent.theme ? parent.theme.accent : "#55b8ff"
        font.pixelSize: parent.theme ? parent.theme.textSmall : 12
        font.weight: Font.DemiBold
        font.letterSpacing: 0.7
    }
    Label {
        text: parent.title
        color: parent.theme ? parent.theme.text : "#edf3fb"
        font.pixelSize: parent.theme ? parent.theme.textTitle : 20
        font.weight: Font.DemiBold
        wrapMode: Text.Wrap
        Layout.fillWidth: true
    }
    Label {
        visible: parent.description.length > 0
        text: parent.description
        color: parent.theme ? parent.theme.mutedText : "#9fb0c7"
        font.pixelSize: parent.theme ? parent.theme.textBody : 14
        wrapMode: Text.Wrap
        Layout.fillWidth: true
    }
}
