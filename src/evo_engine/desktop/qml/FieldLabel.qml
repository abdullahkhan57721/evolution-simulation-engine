import QtQuick
import QtQuick.Controls

Label {
    property var theme
    color: theme ? theme.mutedText : "#9fb0c7"
    font.pixelSize: theme ? theme.textSmall : 12
    font.weight: Font.DemiBold
}
