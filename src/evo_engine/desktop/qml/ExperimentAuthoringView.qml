import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ScrollView {
    id: root
    property var theme
    property var app
    property var experiment
    contentWidth: availableWidth
    clip: true

    ColumnLayout {
        width: root.width
        spacing: theme.space3

        SectionHeader {
            theme: root.theme
            eyebrow: "Study / Experiment"
            title: "Experiment"
            description: "Author only the concrete controlled-experiment definitions already supported by the Workbench. Expanded rows below are authoritative previews of the run matrix."
            Layout.fillWidth: true
        }

        SurfacePanel {
            theme: root.theme
            visible: experiment.mode === "e3"
            Layout.fillWidth: true
            implicitHeight: e3Content.implicitHeight + theme.space4 * 2
            ColumnLayout {
                id: e3Content
                anchors.fill: parent
                anchors.margins: theme.space4
                spacing: theme.space3

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Maximum-speed sweep"; color: theme.text; font.pixelSize: 17; font.weight: Font.DemiBold; Layout.fillWidth: true }
                    StatusBadge { theme: root.theme; text: experiment.draftDirty ? "UNSAVED DESIGN" : "EXACT DEFINITION"; tone: experiment.draftDirty ? "warning" : "success" }
                }
                Label { text: "Factor: " + experiment.factorLabel + " · Base resource geography: " + experiment.baseResourceGeography; color: theme.mutedText; Layout.fillWidth: true; wrapMode: Text.Wrap }

                FieldLabel { theme: root.theme; text: "FACTOR LEVELS" }
                Flow {
                    Layout.fillWidth: true
                    spacing: theme.space2
                    Repeater {
                        model: experiment.factorLevelModel
                        delegate: CheckBox {
                            required property int levelValue
                            required property bool selected
                            text: "Maximum speed " + levelValue
                            checked: selected
                            onClicked: experiment.setE3LevelSelected(levelValue, checked)
                        }
                    }
                }

                FieldLabel { theme: root.theme; text: "REPLICATE SEEDS" }
                TextField {
                    Layout.fillWidth: true
                    text: experiment.replicateSeedsText
                    placeholderText: "101, 202, 303"
                    onEditingFinished: experiment.setReplicateSeeds(text)
                }

                DiagnosticBanner {
                    theme: root.theme
                    visible: experiment.validationMessage.length > 0
                    tone: "warning"
                    title: "Experiment draft is invalid"
                    message: experiment.validationMessage
                    Layout.fillWidth: true
                }

                WorkbenchButton {
                    theme: root.theme
                    text: "Apply experiment design"
                    primary: true
                    enabled: experiment.draftDirty && experiment.draftValid && !app.running
                    onClicked: experiment.applyExperimentDesign()
                }
            }
        }

        SurfacePanel {
            theme: root.theme
            visible: experiment.mode === "e4"
            Layout.fillWidth: true
            implicitHeight: e4Content.implicitHeight + theme.space4 * 2
            ColumnLayout {
                id: e4Content
                anchors.fill: parent
                anchors.margins: theme.space4
                spacing: theme.space3

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Environment-selection comparison"; color: theme.text; font.pixelSize: 17; font.weight: Font.DemiBold; Layout.fillWidth: true }
                    StatusBadge { theme: root.theme; text: experiment.draftDirty ? "UNSAVED DESIGN" : "EXACT DEFINITION"; tone: experiment.draftDirty ? "warning" : "success" }
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: theme.space4
                    rowSpacing: theme.space2
                    FieldLabel { theme: root.theme; text: "CONTROL ENVIRONMENT" }
                    Label { text: experiment.controlEnvironment; color: theme.mutedText }
                    FieldLabel { theme: root.theme; text: "TREATMENT ENVIRONMENT" }
                    Label { text: experiment.treatmentEnvironment; color: theme.mutedText }
                    FieldLabel { theme: root.theme; text: "STANDING FOCAL COMPOSITION" }
                    Label { text: experiment.standingComposition; color: theme.mutedText }
                    FieldLabel { theme: root.theme; text: "COUNTERBALANCE" }
                    Label { text: experiment.counterbalanceLabel; color: theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                }

                FieldLabel { theme: root.theme; text: "MATCHED REPLICATE SEEDS" }
                TextField {
                    Layout.fillWidth: true
                    text: experiment.replicateSeedsText
                    placeholderText: "11, 22, 33"
                    onEditingFinished: experiment.setReplicateSeeds(text)
                }

                DiagnosticBanner {
                    theme: root.theme
                    visible: experiment.validationMessage.length > 0
                    tone: "warning"
                    title: "Experiment draft is invalid"
                    message: experiment.validationMessage
                    Layout.fillWidth: true
                }

                WorkbenchButton {
                    theme: root.theme
                    text: "Apply matched-arm design"
                    primary: true
                    enabled: experiment.draftDirty && experiment.draftValid && !app.running
                    onClicked: experiment.applyExperimentDesign()
                }
            }
        }

        SurfacePanel {
            theme: root.theme
            visible: experiment.mode === "b3"
            Layout.fillWidth: true
            implicitHeight: b3Content.implicitHeight + theme.space4 * 2
            ColumnLayout {
                id: b3Content
                anchors.fill: parent
                anchors.margins: theme.space4
                spacing: theme.space3
                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "B3 flagship compiled design"; color: theme.text; font.pixelSize: 17; font.weight: Font.DemiBold; Layout.fillWidth: true }
                    StatusBadge { theme: root.theme; text: "CURATED · READ ONLY"; tone: "neutral" }
                }
                Label { text: "The flagship experiment remains a fixed validated design; Q2 reports its compiled case counts rather than inventing a generic experiment editor."; color: theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                GridLayout {
                    columns: 2
                    columnSpacing: theme.space4
                    rowSpacing: theme.space2
                    FieldLabel { theme: root.theme; text: "CONFIRMATION PAIRS" }
                    Label { text: experiment.b3ConfirmationPairs; color: theme.text }
                    FieldLabel { theme: root.theme; text: "RADIUS-SENSITIVITY RUNS" }
                    Label { text: experiment.b3RadiusSensitivityRuns; color: theme.text }
                    FieldLabel { theme: root.theme; text: "COUNTERBALANCED PAIRS" }
                    Label { text: experiment.b3CounterbalancedPairs; color: theme.text }
                    FieldLabel { theme: root.theme; text: "TOTAL SIMULATIONS" }
                    Label { text: experiment.b3TotalSimulations; color: theme.text; font.weight: Font.DemiBold }
                }
            }
        }

        DiagnosticBanner {
            theme: root.theme
            visible: experiment.mode === "controlled-single" || experiment.mode === "reference-single"
            tone: "neutral"
            title: "Single-run Study"
            message: experiment.singleRunMessage
            Layout.fillWidth: true
        }

        SurfacePanel {
            theme: root.theme
            visible: experiment.mode === "e3" || experiment.mode === "e4"
            Layout.fillWidth: true
            implicitHeight: matrixContent.implicitHeight + theme.space4 * 2
            ColumnLayout {
                id: matrixContent
                anchors.fill: parent
                anchors.margins: theme.space4
                spacing: theme.space2
                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Authoritative expanded run matrix"; color: theme.text; font.pixelSize: 17; font.weight: Font.DemiBold; Layout.fillWidth: true }
                    StatusBadge { theme: root.theme; text: experiment.totalSimulations + " RUNS"; tone: "neutral" }
                }

                Repeater {
                    model: experiment.runModel
                    delegate: Rectangle {
                        required property string maximumSpeed
                        required property string seed
                        required property string roleName
                        required property string environment
                        required property string resourceGeography
                        required property string standingComposition
                        required property string founderOrder
                        Layout.fillWidth: true
                        implicitHeight: rowText.implicitHeight + theme.space2 * 2
                        radius: theme.radiusSmall
                        color: theme.canvasRaised
                        border.width: 1
                        border.color: theme.border
                        Label {
                            id: rowText
                            anchors.fill: parent
                            anchors.margins: theme.space2
                            text: experiment.mode === "e3"
                                ? "max speed " + maximumSpeed + " · seed " + seed + " · " + resourceGeography
                                : roleName + " · seed " + seed + " · " + environment + " · standing " + standingComposition + " · founder order " + founderOrder
                            color: theme.mutedText
                            wrapMode: Text.Wrap
                        }
                    }
                }
            }
        }
    }
}
