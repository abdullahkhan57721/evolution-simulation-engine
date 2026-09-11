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
        spacing: root.theme.space3

        SectionHeader {
            theme: root.theme
            eyebrow: "Study / Experiment"
            title: "Experiment"
            description: "Author only the concrete controlled-experiment definitions already supported by the Workbench. Expanded rows below are authoritative previews of the run matrix."
            Layout.fillWidth: true
        }

        SurfacePanel {
            theme: root.theme
            visible: root.experiment.mode === "e3"
            Layout.fillWidth: true
            implicitHeight: e3Content.implicitHeight + root.theme.space4 * 2
            ColumnLayout {
                id: e3Content
                anchors.fill: parent
                anchors.margins: root.theme.space4
                spacing: root.theme.space3

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Maximum-speed sweep"; color: root.theme.text; font.pixelSize: 17; font.weight: Font.DemiBold; Layout.fillWidth: true }
                    StatusBadge { theme: root.theme; text: root.experiment.draftDirty ? "UNSAVED DESIGN" : "EXACT DEFINITION"; tone: root.experiment.draftDirty ? "warning" : "success" }
                }
                Label { text: "Factor: " + root.experiment.factorLabel + " · Base resource geography: " + root.experiment.baseResourceGeography; color: root.theme.mutedText; Layout.fillWidth: true; wrapMode: Text.Wrap }

                FieldLabel { theme: root.theme; text: "FACTOR LEVELS" }
                Flow {
                    Layout.fillWidth: true
                    Layout.preferredHeight: childrenRect.height
                    spacing: root.theme.space2
                    Repeater {
                        model: root.experiment.factorLevelModel
                        delegate: CheckBox {
                            required property int levelValue
                            required property bool selected
                            text: "Maximum speed " + levelValue
                            checked: selected
                            activeFocusOnTab: true
                            Accessible.description: "Include this maximum-speed level in the controlled sweep."
                            onClicked: root.experiment.setE3LevelSelected(levelValue, checked)
                        }
                    }
                }

                FieldLabel { theme: root.theme; text: "REPLICATE SEEDS" }
                TextField {
                    Layout.fillWidth: true
                    text: root.experiment.replicateSeedsText
                    placeholderText: "101, 202, 303"
                    activeFocusOnTab: true
                    Accessible.name: "Replicate seeds"
                    onEditingFinished: root.experiment.setReplicateSeeds(text)
                }

                DiagnosticBanner {
                    theme: root.theme
                    visible: root.experiment.validationMessage.length > 0
                    tone: "warning"
                    title: "Experiment draft is invalid"
                    message: root.experiment.validationMessage
                    Layout.fillWidth: true
                }

                WorkbenchButton {
                    theme: root.theme
                    text: "Apply experiment design"
                    primary: true
                    enabled: root.experiment.draftDirty && root.experiment.draftValid && !root.app.running
                    onClicked: root.experiment.applyExperimentDesign()
                }
            }
        }

        SurfacePanel {
            theme: root.theme
            visible: root.experiment.mode === "e4"
            Layout.fillWidth: true
            implicitHeight: e4Content.implicitHeight + root.theme.space4 * 2
            ColumnLayout {
                id: e4Content
                anchors.fill: parent
                anchors.margins: root.theme.space4
                spacing: root.theme.space3

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Environment-selection comparison"; color: root.theme.text; font.pixelSize: 17; font.weight: Font.DemiBold; Layout.fillWidth: true }
                    StatusBadge { theme: root.theme; text: root.experiment.draftDirty ? "UNSAVED DESIGN" : "EXACT DEFINITION"; tone: root.experiment.draftDirty ? "warning" : "success" }
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: root.width >= 720 ? 2 : 1
                    columnSpacing: root.theme.space4
                    rowSpacing: root.theme.space2
                    FieldLabel { theme: root.theme; text: "CONTROL ENVIRONMENT" }
                    Label { text: root.experiment.controlEnvironment; color: root.theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                    FieldLabel { theme: root.theme; text: "TREATMENT ENVIRONMENT" }
                    Label { text: root.experiment.treatmentEnvironment; color: root.theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                    FieldLabel { theme: root.theme; text: "STANDING FOCAL COMPOSITION" }
                    Label { text: root.experiment.standingComposition; color: root.theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                    FieldLabel { theme: root.theme; text: "COUNTERBALANCE" }
                    Label { text: root.experiment.counterbalanceLabel; color: root.theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                }

                FieldLabel { theme: root.theme; text: "MATCHED REPLICATE SEEDS" }
                TextField {
                    Layout.fillWidth: true
                    text: root.experiment.replicateSeedsText
                    placeholderText: "11, 22, 33"
                    activeFocusOnTab: true
                    Accessible.name: "Matched replicate seeds"
                    onEditingFinished: root.experiment.setReplicateSeeds(text)
                }

                DiagnosticBanner {
                    theme: root.theme
                    visible: root.experiment.validationMessage.length > 0
                    tone: "warning"
                    title: "Experiment draft is invalid"
                    message: root.experiment.validationMessage
                    Layout.fillWidth: true
                }

                WorkbenchButton {
                    theme: root.theme
                    text: "Apply matched-arm design"
                    primary: true
                    enabled: root.experiment.draftDirty && root.experiment.draftValid && !root.app.running
                    onClicked: root.experiment.applyExperimentDesign()
                }
            }
        }

        SurfacePanel {
            theme: root.theme
            visible: root.experiment.mode === "b3"
            Layout.fillWidth: true
            implicitHeight: b3Content.implicitHeight + root.theme.space4 * 2
            ColumnLayout {
                id: b3Content
                anchors.fill: parent
                anchors.margins: root.theme.space4
                spacing: root.theme.space3
                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "B3 flagship compiled design"; color: root.theme.text; font.pixelSize: 17; font.weight: Font.DemiBold; Layout.fillWidth: true }
                    StatusBadge { theme: root.theme; text: "CURATED · READ ONLY"; tone: "neutral" }
                }
                Label { text: "The flagship experiment remains a fixed validated design; the native Workbench reports its compiled case counts rather than inventing a generic experiment editor."; color: root.theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                GridLayout {
                    columns: root.width >= 620 ? 2 : 1
                    columnSpacing: root.theme.space4
                    rowSpacing: root.theme.space2
                    FieldLabel { theme: root.theme; text: "CONFIRMATION PAIRS" }
                    Label { text: root.experiment.b3ConfirmationPairs; color: root.theme.text }
                    FieldLabel { theme: root.theme; text: "RADIUS-SENSITIVITY RUNS" }
                    Label { text: root.experiment.b3RadiusSensitivityRuns; color: root.theme.text }
                    FieldLabel { theme: root.theme; text: "COUNTERBALANCED PAIRS" }
                    Label { text: root.experiment.b3CounterbalancedPairs; color: root.theme.text }
                    FieldLabel { theme: root.theme; text: "TOTAL SIMULATIONS" }
                    Label { text: root.experiment.b3TotalSimulations; color: root.theme.text; font.weight: Font.DemiBold }
                }
            }
        }

        DiagnosticBanner {
            theme: root.theme
            visible: root.experiment.mode === "controlled-single" || root.experiment.mode === "reference-single"
            tone: "neutral"
            title: "Single-run Study"
            message: root.experiment.singleRunMessage
            Layout.fillWidth: true
        }

        SurfacePanel {
            theme: root.theme
            visible: root.experiment.mode === "e3" || root.experiment.mode === "e4"
            Layout.fillWidth: true
            implicitHeight: matrixContent.implicitHeight + root.theme.space4 * 2
            ColumnLayout {
                id: matrixContent
                anchors.fill: parent
                anchors.margins: root.theme.space4
                spacing: root.theme.space2
                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Authoritative expanded run matrix"; color: root.theme.text; font.pixelSize: 17; font.weight: Font.DemiBold; Layout.fillWidth: true }
                    StatusBadge { theme: root.theme; text: root.experiment.totalSimulations + " RUNS"; tone: "neutral" }
                }

                Repeater {
                    model: root.experiment.runModel
                    delegate: Rectangle {
                        id: runRow
                        required property string maximumSpeed
                        required property string seed
                        required property string roleName
                        required property string environment
                        required property string resourceGeography
                        required property string standingComposition
                        required property string founderOrder
                        Layout.fillWidth: true
                        implicitHeight: rowText.implicitHeight + root.theme.space2 * 2
                        radius: root.theme.radiusSmall
                        color: root.theme.canvasRaised
                        border.width: 1
                        border.color: root.theme.border
                        Label {
                            id: rowText
                            anchors.fill: parent
                            anchors.margins: root.theme.space2
                            text: root.experiment.mode === "e3"
                                ? "max speed " + runRow.maximumSpeed + " · seed " + runRow.seed + " · " + runRow.resourceGeography
                                : runRow.roleName + " · seed " + runRow.seed + " · " + runRow.environment + " · standing " + runRow.standingComposition + " · founder order " + runRow.founderOrder
                            color: root.theme.mutedText
                            wrapMode: Text.Wrap
                        }
                    }
                }
            }
        }
    }
}
