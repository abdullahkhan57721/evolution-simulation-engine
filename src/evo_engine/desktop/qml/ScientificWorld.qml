import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    required property var organismModel
    required property var resourceModel
    required property var carcassModel
    required property var trailModel
    required property int worldWidth
    required property int worldHeight
    required property int committedStep

    property string title: "World"
    property string subtitle: "Committed scientific frame"
    property string legendLabel: ""
    property int legendLower: 0
    property int legendUpper: 0
    property bool labelsVisible: false
    property bool trailsVisible: false
    property bool focusMode: false
    property bool animatePositions: false
    property int transitionDuration: 300
    property string inspectorTitle: "No organism selected"
    property string inspectorBody: "Select an organism to inspect committed values."
    property real coordinatePadding: 30

    signal organismSelected(int organismId)

    function pointX(worldX) {
        if (worldWidth <= 1)
            return worldCanvas.width / 2
        var padding = Math.min(root.coordinatePadding, worldCanvas.width / 2)
        return padding + (worldX / (worldWidth - 1)) * Math.max(0, worldCanvas.width - 2 * padding)
    }

    function pointY(worldY) {
        if (worldHeight <= 1)
            return worldCanvas.height / 2
        var padding = Math.min(root.coordinatePadding, worldCanvas.height / 2)
        return padding + (worldY / (worldHeight - 1)) * Math.max(0, worldCanvas.height - 2 * padding)
    }

    function traitColor(normalized) {
        if (normalized === null || normalized === undefined)
            return root.theme.organism
        var n = Math.max(0.0, Math.min(1.0, Number(normalized)))
        if (n < 0.5) {
            var local = n * 2.0
            return Qt.rgba(
                0.17 + 0.26 * local,
                0.36 + 0.39 * local,
                0.57 + 0.30 * local,
                1.0
            )
        }
        var upper = (n - 0.5) * 2.0
        return Qt.rgba(
            0.43 + 0.53 * upper,
            0.75 + 0.03 * upper,
            0.87 - 0.50 * upper,
            1.0
        )
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: root.theme.space2

        ColumnLayout {
            Layout.fillWidth: true
            spacing: root.theme.space1

            Label {
                text: root.title
                color: root.theme.text
                font.pixelSize: 16
                font.weight: Font.DemiBold
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
            Label {
                text: root.subtitle
                color: root.theme.mutedText
                font.pixelSize: root.theme.textSmall
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
            Flow {
                Layout.fillWidth: true
                spacing: root.theme.space1
                implicitHeight: childrenRect.height
                StatusBadge {
                    theme: root.theme
                    text: "STEP " + root.committedStep
                    tone: "neutral"
                }
                StatusBadge {
                    theme: root.theme
                    text: root.worldWidth + " × " + root.worldHeight
                    tone: "neutral"
                }
            }
        }

        Rectangle {
            id: worldFrame
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 300
            radius: root.theme.radius
            color: root.theme.canvas
            border.color: root.theme.border
            clip: true

            Rectangle {
                id: worldCanvas
                anchors.fill: parent
                anchors.margins: 18
                color: "#0d1727"
                border.color: "#263a57"
                border.width: 1
                clip: true
                Accessible.name: root.title + ", committed step " + root.committedStep
                Accessible.description: "Recorded scientific world. Tab to organisms and press Enter or Space to inspect committed values."
                Accessible.role: Accessible.Pane

                Repeater {
                    model: root.resourceModel
                    delegate: Rectangle {
                        required property real worldX
                        required property real worldY
                        required property int amount
                        width: Math.max(4, Math.min(12, 3 + Math.sqrt(Math.max(0, amount))))
                        height: width
                        radius: width / 2
                        x: root.pointX(worldX) - width / 2
                        y: root.pointY(worldY) - height / 2
                        color: root.theme.resource
                        opacity: root.focusMode ? 0.18 : 0.62
                        border.color: "#d7f4b7"
                        border.width: 1
                        Accessible.name: "Resource, amount " + amount
                        Accessible.role: Accessible.Graphic
                    }
                }

                Repeater {
                    model: root.carcassModel
                    delegate: Item {
                        id: carcassDelegate
                        required property int carcassId
                        required property real worldX
                        required property real worldY
                        required property int resourceUnits
                        width: 12
                        height: 12
                        x: root.pointX(worldX) - width / 2
                        y: root.pointY(worldY) - height / 2
                        opacity: root.focusMode ? 0.24 : 0.85
                        Accessible.name: "Carcass " + carcassId + ", " + resourceUnits + " resource units"
                        Accessible.role: Accessible.Graphic
                        Rectangle {
                            anchors.centerIn: parent
                            width: parent.width
                            height: 2
                            rotation: 45
                            color: root.theme.warning
                        }
                        Rectangle {
                            anchors.centerIn: parent
                            width: parent.width
                            height: 2
                            rotation: -45
                            color: root.theme.warning
                        }
                        ToolTip.visible: carcassMouse.hovered
                        ToolTip.text: "Carcass " + carcassDelegate.carcassId + " · " + carcassDelegate.resourceUnits + " resource units"
                        HoverHandler { id: carcassMouse }
                    }
                }

                Repeater {
                    model: root.trailsVisible ? root.trailModel : null
                    delegate: Canvas {
                        id: trailCanvas
                        required property int organismId
                        required property var points
                        anchors.fill: parent
                        opacity: root.focusMode ? 0.2 : 0.48
                        Accessible.name: "Recent committed trail for organism " + organismId
                        Accessible.role: Accessible.Graphic

                        onPointsChanged: requestPaint()
                        onWidthChanged: requestPaint()
                        onHeightChanged: requestPaint()

                        onPaint: {
                            var ctx = getContext("2d")
                            ctx.clearRect(0, 0, width, height)
                            if (!points || points.length < 2)
                                return
                            ctx.beginPath()
                            ctx.lineWidth = 1.5
                            ctx.strokeStyle = "#91a8c7"
                            ctx.moveTo(root.pointX(points[0].x), root.pointY(points[0].y))
                            for (var i = 1; i < points.length; ++i)
                                ctx.lineTo(root.pointX(points[i].x), root.pointY(points[i].y))
                            ctx.stroke()
                        }
                    }
                }

                Repeater {
                    model: root.organismModel
                    delegate: Item {
                        id: organismDelegate
                        required property int organismId
                        required property real worldX
                        required property real worldY
                        required property int markerSize
                        required property bool selected
                        required property int bodyMass
                        required property int energy
                        required property int age
                        required property string matingType
                        required property var focalTraitValue
                        required property var focalTraitNormalized

                        width: markerSize + 16
                        height: markerSize + (root.labelsVisible ? 24 : 16)
                        x: root.pointX(worldX) - width / 2
                        y: root.pointY(worldY) - markerSize / 2
                        opacity: root.focusMode && !selected && !activeFocus ? 0.2 : 1.0
                        activeFocusOnTab: true
                        Accessible.name: "Organism " + organismId
                        Accessible.description: "Age " + age + ", energy " + energy + ", body mass " + bodyMass + ", mating type " + matingType
                            + (focalTraitValue === null || focalTraitValue === undefined ? "" : ", focal trait " + focalTraitValue)
                            + (selected ? ". Selected for inspection." : ".")
                        Accessible.role: Accessible.Button
                        Accessible.selected: selected
                        Accessible.onPressAction: root.organismSelected(organismId)
                        Keys.onReturnPressed: root.organismSelected(organismId)
                        Keys.onEnterPressed: root.organismSelected(organismId)
                        Keys.onSpacePressed: root.organismSelected(organismId)

                        Behavior on x {
                            enabled: root.animatePositions
                            NumberAnimation {
                                duration: root.transitionDuration
                                easing.type: Easing.InOutCubic
                            }
                        }
                        Behavior on y {
                            enabled: root.animatePositions
                            NumberAnimation {
                                duration: root.transitionDuration
                                easing.type: Easing.InOutCubic
                            }
                        }

                        Rectangle {
                            anchors.horizontalCenter: marker.horizontalCenter
                            anchors.verticalCenter: marker.verticalCenter
                            width: marker.width + 15
                            height: width
                            radius: width / 2
                            color: "transparent"
                            border.color: root.theme.focus
                            border.width: organismDelegate.activeFocus ? 2 : 0
                            visible: organismDelegate.activeFocus
                        }

                        Rectangle {
                            id: selectionHalo
                            anchors.horizontalCenter: marker.horizontalCenter
                            anchors.verticalCenter: marker.verticalCenter
                            width: marker.width + 9
                            height: width
                            radius: width / 2
                            color: "transparent"
                            border.color: root.theme.selected
                            border.width: organismDelegate.selected ? 3 : 0
                            visible: organismDelegate.selected
                        }

                        Rectangle {
                            id: marker
                            width: organismDelegate.markerSize
                            height: organismDelegate.markerSize
                            radius: width / 2
                            anchors.top: parent.top
                            anchors.horizontalCenter: parent.horizontalCenter
                            color: root.traitColor(organismDelegate.focalTraitNormalized)
                            border.color: organismDelegate.selected ? "#fff4c2" : "#d9e7f7"
                            border.width: organismDelegate.selected ? 2 : 1

                            Label {
                                anchors.centerIn: parent
                                visible: organismDelegate.focalTraitValue !== null && organismDelegate.focalTraitValue !== undefined && marker.width >= 18
                                text: organismDelegate.focalTraitValue === null || organismDelegate.focalTraitValue === undefined ? "" : organismDelegate.focalTraitValue
                                color: "#06121e"
                                font.pixelSize: Math.max(8, Math.min(11, marker.width * 0.45))
                                font.weight: Font.Bold
                            }
                        }

                        Label {
                            anchors.top: marker.bottom
                            anchors.topMargin: 3
                            anchors.horizontalCenter: marker.horizontalCenter
                            visible: root.labelsVisible
                            text: "#" + organismDelegate.organismId
                            color: organismDelegate.selected ? root.theme.selected : root.theme.mutedText
                            font.pixelSize: 10
                        }

                        TapHandler {
                            onTapped: root.organismSelected(organismDelegate.organismId)
                        }
                        HoverHandler { id: organismHover }
                        ToolTip.visible: organismHover.hovered
                        ToolTip.text: "Organism " + organismDelegate.organismId + " · age " + organismDelegate.age + " · energy " + organismDelegate.energy
                    }
                }

                Label {
                    anchors.left: parent.left
                    anchors.bottom: parent.bottom
                    anchors.margins: 7
                    text: "Recorded x/y coordinates · animation is presentation only"
                    color: root.theme.subtleText
                    font.pixelSize: 10
                    z: 20
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: root.width >= 520 ? 2 : 1
            columnSpacing: root.theme.space3
            rowSpacing: root.theme.space2

            SurfacePanel {
                theme: root.theme
                Layout.fillWidth: true
                Layout.preferredHeight: legendContent.implicitHeight + root.theme.space2 * 2
                ColumnLayout {
                    id: legendContent
                    anchors.fill: parent
                    anchors.margins: root.theme.space2
                    spacing: 4
                    Label {
                        text: root.legendLabel.length > 0 ? root.legendLabel : "Scientific encoding"
                        color: root.theme.text
                        font.pixelSize: root.theme.textSmall
                        font.weight: Font.DemiBold
                    }
                    RowLayout {
                        visible: root.legendUpper > root.legendLower
                        Layout.fillWidth: true
                        spacing: 6
                        Label { text: root.legendLower; color: root.theme.mutedText; font.pixelSize: 10 }
                        Rectangle {
                            Layout.fillWidth: true
                            height: 9
                            radius: 4
                            gradient: Gradient {
                                orientation: Gradient.Horizontal
                                GradientStop { position: 0.0; color: root.traitColor(0.0) }
                                GradientStop { position: 0.5; color: root.traitColor(0.5) }
                                GradientStop { position: 1.0; color: root.traitColor(1.0) }
                            }
                        }
                        Label { text: root.legendUpper; color: root.theme.mutedText; font.pixelSize: 10 }
                    }
                    Label {
                        text: "Selection = gold outline/halo and inspector text · trails = recent committed positions"
                        color: root.theme.subtleText
                        font.pixelSize: 10
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                }
            }

            SurfacePanel {
                theme: root.theme
                Layout.fillWidth: true
                Layout.preferredHeight: inspectorContent.implicitHeight + root.theme.space2 * 2
                Accessible.name: root.inspectorTitle + ". " + root.inspectorBody
                Accessible.role: Accessible.StaticText
                ColumnLayout {
                    id: inspectorContent
                    anchors.fill: parent
                    anchors.margins: root.theme.space2
                    spacing: 4
                    Label {
                        text: root.inspectorTitle
                        color: root.theme.text
                        font.pixelSize: root.theme.textSmall
                        font.weight: Font.DemiBold
                    }
                    Label {
                        text: root.inspectorBody
                        color: root.theme.mutedText
                        font.pixelSize: 10
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                }
            }
        }
    }
}
