import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 1180
    height: 780
    minimumWidth: 900
    minimumHeight: 620
    visible: true
    title: "Evolution Experiment Workbench"

    // Q0 tokens only: one calm light scientific surface hierarchy.
    readonly property color canvasColor: "#f4f6f8"
    readonly property color surfaceColor: "#ffffff"
    readonly property color borderColor: "#d8dee6"
    readonly property color textColor: "#17212b"
    readonly property color mutedTextColor: "#5b6775"
    readonly property color accentColor: "#2563eb"
    readonly property color selectionColor: "#f59e0b"
    readonly property color warningColor: "#a16207"
    readonly property int space1: 6
    readonly property int space2: 12
    readonly property int space3: 18
    readonly property int radius: 10

    background: Rectangle { color: root.canvasColor }

    FileDialog {
        id: openDialog
        title: "Open exact Study revision"
        fileMode: FileDialog.OpenFile
        nameFilters: ["Workbench Study (*.json)", "JSON files (*.json)"]
        onAccepted: studyController.openStudy(selectedFile.toString())
    }

    FileDialog {
        id: saveDialog
        title: "Save exact Study revision"
        fileMode: FileDialog.SaveFile
        defaultSuffix: "json"
        nameFilters: ["Workbench Study (*.json)"]
        onAccepted: studyController.saveStudy(selectedFile.toString())
    }

    header: Rectangle {
        implicitHeight: 66
        color: root.surfaceColor
        border.color: root.borderColor
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: root.space3
            anchors.rightMargin: root.space3
            spacing: root.space2
            Label {
                text: "Evolution Experiment Workbench"
                color: root.textColor
                font.pixelSize: 20
                font.bold: true
                Layout.fillWidth: true
            }
            Button { text: "New Study"; enabled: !studyController.running; onClicked: studyController.createStudy() }
            Button { text: "Open…"; enabled: !studyController.running; onClicked: openDialog.open() }
            Button { text: "Save…"; enabled: studyController.hasStudy; onClicked: saveDialog.open() }
        }
    }

    ScrollView {
        anchors.fill: parent
        anchors.margins: root.space3
        contentWidth: availableWidth

        ColumnLayout {
            width: parent.width
            spacing: root.space3

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: studyHeader.implicitHeight + root.space3 * 2
                color: root.surfaceColor
                radius: root.radius
                border.color: root.borderColor
                ColumnLayout {
                    id: studyHeader
                    anchors.fill: parent
                    anchors.margins: root.space3
                    spacing: root.space1
                    Label {
                        text: studyController.hasStudy ? "REFERENCE ECOLOGY STUDY" : "HOME"
                        color: root.accentColor
                        font.pixelSize: 12
                        font.bold: true
                    }
                    Label {
                        text: studyController.hasStudy ? studyController.revisionId : "Create or open one supported Study"
                        color: root.textColor
                        font.pixelSize: 22
                        font.bold: true
                    }
                    Label {
                        visible: studyController.hasStudy
                        text: "Parent: " + (studyController.parentRevisionId || "—") + "    Manifest: " + studyController.manifestDigest.slice(0, 16) + "…"
                        color: root.mutedTextColor
                        font.pixelSize: 12
                    }
                }
            }

            GridLayout {
                Layout.fillWidth: true
                columns: root.width >= 1050 ? 2 : 1
                columnSpacing: root.space3
                rowSpacing: root.space3

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 390
                    color: root.surfaceColor
                    radius: root.radius
                    border.color: root.borderColor
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: root.space3
                        spacing: root.space2
                        Label { text: "Simulation"; color: root.textColor; font.pixelSize: 18; font.bold: true }
                        Label { text: "One supported semantic choice"; color: root.mutedTextColor }
                        RowLayout {
                            Layout.fillWidth: true
                            Label { text: "Founder maximum speed"; color: root.textColor; Layout.fillWidth: true }
                            SpinBox {
                                from: 0
                                to: 4
                                value: studyController.draftMaxSpeed
                                enabled: studyController.hasStudy && !studyController.running
                                onValueModified: studyController.draftMaxSpeed = value
                            }
                        }
                        Label {
                            text: studyController.draftDirty ? "Unsaved semantic draft" : "Exact saved revision"
                            color: studyController.draftDirty ? root.warningColor : root.mutedTextColor
                            font.bold: studyController.draftDirty
                        }
                        Label { text: "Explicit meaning"; color: root.textColor; font.bold: true }
                        Label {
                            text: studyController.explicitMeaning
                            color: root.mutedTextColor
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                            Layout.maximumHeight: 70
                            elide: Text.ElideRight
                        }
                        Label { text: "Derived meaning"; color: root.textColor; font.bold: true }
                        Label {
                            text: studyController.derivedMeaning
                            color: root.mutedTextColor
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                            Layout.maximumHeight: 70
                            elide: Text.ElideRight
                        }
                        Item { Layout.fillHeight: true }
                        RowLayout {
                            Layout.fillWidth: true
                            Button {
                                text: "Save child revision"
                                enabled: studyController.draftDirty && studyController.draftReady && !studyController.running
                                onClicked: studyController.saveChildRevision()
                            }
                            Item { Layout.fillWidth: true }
                            Button {
                                text: studyController.running ? "Running…" : "Run"
                                highlighted: true
                                enabled: studyController.hasStudy && !studyController.draftDirty && !studyController.running
                                onClicked: studyController.runStudy()
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 390
                    color: root.surfaceColor
                    radius: root.radius
                    border.color: root.borderColor
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: root.space3
                        spacing: root.space2
                        RowLayout {
                            Layout.fillWidth: true
                            Label { text: "Results / Native world"; color: root.textColor; font.pixelSize: 18; font.bold: true; Layout.fillWidth: true }
                            Label { text: studyController.hasResult ? "Final population: " + studyController.finalPopulation : "No result yet"; color: root.mutedTextColor }
                        }
                        Rectangle {
                            id: worldCanvas
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: "#edf2f7"
                            radius: root.radius
                            border.color: root.borderColor
                            clip: true

                            Label {
                                anchors.centerIn: parent
                                visible: !studyController.hasResult
                                text: "Run the saved revision to render an authoritative WorldPresentationFrame."
                                color: root.mutedTextColor
                            }

                            Repeater {
                                model: studyController.resourceModel
                                delegate: Rectangle {
                                    width: Math.max(3, Math.min(10, 2 + amount / 4))
                                    height: width
                                    radius: width / 2
                                    color: "#65a30d"
                                    opacity: 0.5
                                    x: (worldX + 0.5) / Math.max(1, studyController.worldWidth) * worldCanvas.width - width / 2
                                    y: (worldY + 0.5) / Math.max(1, studyController.worldHeight) * worldCanvas.height - height / 2
                                }
                            }

                            Repeater {
                                model: studyController.organismModel
                                delegate: Rectangle {
                                    width: markerSize
                                    height: markerSize
                                    radius: width / 2
                                    color: selected ? root.selectionColor : root.accentColor
                                    border.width: selected ? 3 : 1
                                    border.color: selected ? "#7c2d12" : "#ffffff"
                                    x: (worldX + 0.5) / Math.max(1, studyController.worldWidth) * worldCanvas.width - width / 2
                                    y: (worldY + 0.5) / Math.max(1, studyController.worldHeight) * worldCanvas.height - height / 2
                                    ToolTip.visible: hover.hovered
                                    ToolTip.text: "Organism " + organismId + " · mass " + bodyMass + " · energy " + energy
                                    HoverHandler { id: hover }
                                    TapHandler { onTapped: studyController.selectOrganism(organismId) }
                                }
                            }

                            Label {
                                anchors.left: parent.left
                                anchors.bottom: parent.bottom
                                anchors.margins: root.space1
                                visible: studyController.hasResult
                                text: "Committed step " + studyController.worldStep + " · " + studyController.worldWidth + " × " + studyController.worldHeight
                                color: root.mutedTextColor
                                font.pixelSize: 11
                            }
                        }
                    }
                }
            }

            Label {
                Layout.fillWidth: true
                text: studyController.status
                color: root.mutedTextColor
                wrapMode: Text.Wrap
            }
        }
    }
}
