import QtQuick

Rectangle {
    property var theme
    color: theme ? theme.surface : "#162033"
    radius: theme ? theme.radius : 12
    border.width: 1
    border.color: theme ? theme.border : "#2a3a55"
}
