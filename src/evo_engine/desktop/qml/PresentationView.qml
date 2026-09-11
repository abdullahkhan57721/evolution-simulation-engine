import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    required property var app
    required property var presentation

    Timer {
        interval: root.presentation.playbackIntervalMs
        running: root.presentation.playing
        repeat: true
        onTriggered: root.presentation.advancePlayback()
    }

    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth
        clip: true

        ColumnLayout {
            width: root.width
            spacing: root.theme.space3

            SectionHeader {
                theme: root.theme
                eyebrow: "Study / Presentation"
                title: "Scientific world replay"
                description: "Every exact timeline stop is an authoritative committed frame. Motion between adjacent stops is renderer choreography only and never becomes scientific evidence."
                Layout.fillWidth: true
            }

            DiagnosticBanner {
                theme: root.theme
                visible: !root.presentation.available
                tone: root.presentation.remediation.length > 0 ? "warning" : "neutral"
                title: root.app.hasResult ? "World replay unavailable" : "No current-session result"
                message: root.presentation.message
                remediation: root.presentation.remediation
                Layout.fillWidth: true
            }

            ColumnLayout {
                visible: root.presentation.available
                Layout.fillWidth: true
                spacing: root.theme.space3

                SurfacePanel {
                    theme: root.theme
                    Layout.fillWidth: true
                    implicitHeight: controls.implicitHeight + root.theme.space3 * 2

                    ColumnLayout {
                        id: controls
                        anchors.fill: parent
                        anchors.margins: root.theme.space3
                        spacing: root.theme.space2

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: root.theme.space2

                            StatusBadge {
                                theme: root.theme
                                text: "COMMITTED STEP " + root.presentation.committedStep
                                tone: "success"
                            }
                            StatusBadge {
                                theme: root.theme
                                text: root.presentation.family === "b3" ? "MATCHED B3" : "REFERENCE REPLAY"
                                tone: "neutral"
                            }
                            Item { Layout.fillWidth: true }
                            WorkbenchButton {
                                theme: root.theme
                                text: root.presentation.labelsVisible ? "Labels on" : "Labels off"
                                onClicked: root.presentation.toggleLabels()
                            }
                            WorkbenchButton {
                                theme: root.theme
                                text: root.presentation.trailsVisible ? "Trails on" : "Trails off"
                                onClicked: root.presentation.toggleTrails()
                            }
                            WorkbenchButton {
                                theme: root.theme
                                primary: root.presentation.focusMode
                                text: root.presentation.focusMode ? "Exit Focus" : "Focus Mode"
                                onClicked: root.presentation.toggleFocusMode()
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: root.theme.space2

                            WorkbenchButton {
                                theme: root.theme
                                text: "Previous"
                                enabled: root.presentation.canPrevious
                                onClicked: root.presentation.previousStep()
                            }
                            WorkbenchButton {
                                theme: root.theme
                                primary: true
                                text: root.presentation.playing ? "Pause" : "Play"
                                enabled: root.presentation.stepCount > 1
                                onClicked: root.presentation.togglePlayback()
                            }
                            WorkbenchButton {
                                theme: root.theme
                                text: "Next"
                                enabled: root.presentation.canNext
                                onClicked: root.presentation.nextStep()
                            }

                            Slider {
                                id: timeline
                                Layout.fillWidth: true
                                from: 0
                                to: Math.max(0, root.presentation.stepCount - 1)
                                stepSize: 1
                                snapMode: Slider.SnapAlways
                                value: root.presentation.stepPosition
                                enabled: root.presentation.stepCount > 1
                                onMoved: root.presentation.seekStepPosition(Math.round(value))
                                ToolTip.visible: hovered
                                ToolTip.text: "Exact committed frame position " + Math.round(value)
                            }

                            Label {
                                text: (root.presentation.stepPosition + 1) + " / " + root.presentation.stepCount
                                color: root.theme.mutedText
                                font.pixelSize: root.theme.textSmall
                            }

                            Label {
                                text: "Speed"
                                color: root.theme.subtleText
                                font.pixelSize: root.theme.textSmall
                            }
                            ComboBox {
                                id: speedChoice
                                model: ["0.5×", "1×", "2×", "4×"]
                                currentIndex: root.presentation.playbackSpeed === 0.5
                                    ? 0
                                    : root.presentation.playbackSpeed === 1.0
                                        ? 1
                                        : root.presentation.playbackSpeed === 2.0 ? 2 : 3
                                onActivated: {
                                    var speeds = [0.5, 1.0, 2.0, 4.0]
                                    root.presentation.setPlaybackSpeed(speeds[currentIndex])
                                }
                            }
                        }
                    }
                }

                DiagnosticBanner {
                    theme: root.theme
                    visible: root.presentation.family === "b3"
                    tone: "neutral"
                    title: "Matched scientific comparison"
                    message: root.presentation.matchedLanguage
                    Layout.fillWidth: true
                }

                SurfacePanel {
                    theme: root.theme
                    visible: root.presentation.family === "b3"
                    Layout.fillWidth: true
                    implicitHeight: seedControls.implicitHeight + root.theme.space2 * 2
                    RowLayout {
                        id: seedControls
                        anchors.fill: parent
                        anchors.margins: root.theme.space2
                        spacing: root.theme.space2
                        Label {
                            text: "Confirmation seed " + root.presentation.b3Seed
                            color: root.theme.text
                            font.pixelSize: root.theme.textSmall
                            font.weight: Font.DemiBold
                        }
                        Label {
                            text: "One seed, one common committed step, two independently constructed arm frames."
                            color: root.theme.mutedText
                            font.pixelSize: root.theme.textSmall
                            Layout.fillWidth: true
                            wrapMode: Text.Wrap
                        }
                        WorkbenchButton {
                            theme: root.theme
                            text: "Previous seed"
                            enabled: root.presentation.canPreviousSeed
                            onClicked: root.presentation.previousB3Seed()
                        }
                        WorkbenchButton {
                            theme: root.theme
                            text: "Next seed"
                            enabled: root.presentation.canNextSeed
                            onClicked: root.presentation.nextB3Seed()
                        }
                    }
                }

                ScientificWorld {
                    visible: root.presentation.family === "reference"
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.max(540, root.height - 230)
                    theme: root.theme
                    title: "Reference Ecology"
                    subtitle: "Recorded spatial evidence · exact committed step"
                    organismModel: root.presentation.organismModel
                    resourceModel: root.presentation.resourceModel
                    carcassModel: root.presentation.carcassModel
                    trailModel: root.presentation.trailModel
                    worldWidth: root.presentation.worldWidth
                    worldHeight: root.presentation.worldHeight
                    committedStep: root.presentation.committedStep
                    legendLabel: root.presentation.legendLabel
                    legendLower: root.presentation.legendLower
                    legendUpper: root.presentation.legendUpper
                    labelsVisible: root.presentation.labelsVisible
                    trailsVisible: root.presentation.trailsVisible
                    focusMode: root.presentation.focusMode
                    animatePositions: root.presentation.transitionAnimated
                    transitionDuration: root.presentation.transitionDurationMs
                    inspectorTitle: root.presentation.inspectorTitle
                    inspectorBody: root.presentation.inspectorBody
                    onOrganismSelected: organismId => root.presentation.selectOrganism(organismId)
                }

                RowLayout {
                    visible: root.presentation.family === "b3"
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.max(530, root.height - 245)
                    spacing: root.theme.space3

                    ScientificWorld {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        theme: root.theme
                        title: "Control"
                        subtitle: "Uniform environment · seed " + root.presentation.b3Seed
                        organismModel: root.presentation.controlOrganismModel
                        resourceModel: root.presentation.controlResourceModel
                        carcassModel: root.presentation.controlCarcassModel
                        trailModel: root.presentation.controlTrailModel
                        worldWidth: root.presentation.worldWidth
                        worldHeight: root.presentation.worldHeight
                        committedStep: root.presentation.committedStep
                        legendLabel: root.presentation.legendLabel
                        legendLower: root.presentation.legendLower
                        legendUpper: root.presentation.legendUpper
                        labelsVisible: root.presentation.labelsVisible
                        trailsVisible: root.presentation.trailsVisible
                        focusMode: root.presentation.focusMode
                        animatePositions: root.presentation.transitionAnimated
                        transitionDuration: root.presentation.transitionDurationMs
                        inspectorTitle: root.presentation.controlInspectorTitle
                        inspectorBody: root.presentation.controlInspectorBody
                        onOrganismSelected: organismId => root.presentation.selectControlOrganism(organismId)
                    }

                    ScientificWorld {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        theme: root.theme
                        title: "Treatment"
                        subtitle: "Compact-patch environment · seed " + root.presentation.b3Seed
                        organismModel: root.presentation.treatmentOrganismModel
                        resourceModel: root.presentation.treatmentResourceModel
                        carcassModel: root.presentation.treatmentCarcassModel
                        trailModel: root.presentation.treatmentTrailModel
                        worldWidth: root.presentation.worldWidth
                        worldHeight: root.presentation.worldHeight
                        committedStep: root.presentation.committedStep
                        legendLabel: root.presentation.legendLabel
                        legendLower: root.presentation.legendLower
                        legendUpper: root.presentation.legendUpper
                        labelsVisible: root.presentation.labelsVisible
                        trailsVisible: root.presentation.trailsVisible
                        focusMode: root.presentation.focusMode
                        animatePositions: root.presentation.transitionAnimated
                        transitionDuration: root.presentation.transitionDurationMs
                        inspectorTitle: root.presentation.treatmentInspectorTitle
                        inspectorBody: root.presentation.treatmentInspectorBody
                        onOrganismSelected: organismId => root.presentation.selectTreatmentOrganism(organismId)
                    }
                }

                Label {
                    Layout.fillWidth: true
                    text: "Scientific truth: recorded committed positions and trait values. Presentation only: interpolation, labels, trails visibility, selection halo, focus, and playback timing."
                    color: root.theme.subtleText
                    font.pixelSize: root.theme.textSmall
                    wrapMode: Text.Wrap
                }
            }
        }
    }
}
