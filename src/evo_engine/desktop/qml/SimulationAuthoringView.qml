import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ScrollView {
    id: root
    property var theme
    property var app
    property var reference
    property var simulation
    contentWidth: availableWidth
    clip: true

    ColumnLayout {
        width: root.width
        spacing: theme.space3

        SectionHeader {
            theme: root.theme
            eyebrow: "Study / Simulation"
            title: "Simulation"
            description: "Edit only the stable semantic choices owned by the active Workbench recipe. Saved changes create immutable child revisions."
            Layout.fillWidth: true
        }

        SurfacePanel {
            theme: root.theme
            visible: app.artifactKind === "controlled-run"
            Layout.fillWidth: true
            implicitHeight: controlledContent.implicitHeight + theme.space4 * 2
            ColumnLayout {
                id: controlledContent
                anchors.fill: parent
                anchors.margins: theme.space4
                spacing: theme.space3

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Controlled locomotion"; color: theme.text; font.pixelSize: 17; font.weight: Font.DemiBold; Layout.fillWidth: true }
                    StatusBadge { theme: root.theme; text: simulation.controlledDraftDirty ? "UNSAVED DRAFT" : "EXACT SAVED REVISION"; tone: simulation.controlledDraftDirty ? "warning" : "success" }
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: theme.space4
                    rowSpacing: theme.space2

                    FieldLabel { theme: root.theme; text: "FOUNDER MAXIMUM SPEED" }
                    SpinBox {
                        from: simulation.controlledMinimumMaxSpeed
                        to: simulation.controlledMaximumMaxSpeed
                        value: simulation.controlledMaxSpeed
                        onValueModified: simulation.controlledMaxSpeed = value
                    }
                    FieldLabel { theme: root.theme; text: "RESOURCE GEOGRAPHY" }
                    ComboBox {
                        model: ["Local resource", "Separated corridor"]
                        currentIndex: simulation.controlledResourceGeography === simulation.controlledGeographySecondary ? 1 : 0
                        onActivated: simulation.controlledResourceGeography = currentIndex === 1 ? simulation.controlledGeographySecondary : simulation.controlledGeographyPrimary
                    }
                    FieldLabel { theme: root.theme; text: "RANDOM SEED" }
                    SpinBox {
                        from: -2147483647
                        to: 2147483647
                        value: simulation.controlledSeed
                        onValueModified: simulation.controlledSeed = value
                    }
                }

                DiagnosticBanner {
                    theme: root.theme
                    visible: simulation.controlledReadinessMessage.length > 0
                    tone: simulation.controlledDraftReady ? "neutral" : "warning"
                    title: simulation.controlledDraftReady ? "Scientific draft ready" : "Scientific draft needs attention"
                    message: simulation.controlledReadinessMessage
                    Layout.fillWidth: true
                }

                WorkbenchButton {
                    theme: root.theme
                    text: "Save child revision"
                    primary: true
                    enabled: simulation.controlledDraftDirty && simulation.controlledDraftReady && !app.running
                    onClicked: simulation.saveControlledChildRevision()
                }
            }
        }

        SurfacePanel {
            theme: root.theme
            visible: app.artifactKind === "reference-ecology"
            Layout.fillWidth: true
            implicitHeight: referenceContent.implicitHeight + theme.space4 * 2
            ColumnLayout {
                id: referenceContent
                anchors.fill: parent
                anchors.margins: theme.space4
                spacing: theme.space3

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Reference Ecology · Guided"; color: theme.text; font.pixelSize: 17; font.weight: Font.DemiBold; Layout.fillWidth: true }
                    StatusBadge { theme: root.theme; text: reference.draftDirty ? "UNSAVED DRAFT" : "EXACT SAVED REVISION"; tone: reference.draftDirty ? "warning" : "success" }
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: 4
                    columnSpacing: theme.space3
                    rowSpacing: theme.space2

                    FieldLabel { theme: root.theme; text: "WORLD WIDTH" }
                    SpinBox { from: 4; to: 50; value: reference.draftWorldWidth; onValueModified: reference.draftWorldWidth = value }
                    FieldLabel { theme: root.theme; text: "WORLD HEIGHT" }
                    SpinBox { from: 4; to: 50; value: reference.draftWorldHeight; onValueModified: reference.draftWorldHeight = value }

                    FieldLabel { theme: root.theme; text: "FOUNDER POPULATION" }
                    SpinBox { from: 2; to: 100; value: reference.draftFounderPopulation; onValueModified: reference.draftFounderPopulation = value }
                    FieldLabel { theme: root.theme; text: "FOUNDER STARTING ENERGY" }
                    SpinBox { from: 1; to: 200; value: reference.draftFounderEnergy; onValueModified: reference.draftFounderEnergy = value }

                    FieldLabel { theme: root.theme; text: "RUN HORIZON" }
                    SpinBox { from: 1; to: 500; value: reference.draftHorizon; onValueModified: reference.draftHorizon = value }
                    FieldLabel { theme: root.theme; text: "RANDOM SEED" }
                    SpinBox { from: -2147483647; to: 2147483647; value: reference.draftSeed; onValueModified: reference.draftSeed = value }

                    FieldLabel { theme: root.theme; text: "FOUNDER MAXIMUM SPEED" }
                    SpinBox { from: 0; to: 4; value: reference.draftMaxSpeed; onValueModified: reference.draftMaxSpeed = value }
                    FieldLabel { theme: root.theme; text: "FOUNDER SENSORY RANGE" }
                    SpinBox { from: 0; to: 20; value: reference.draftSensoryRange; onValueModified: reference.draftSensoryRange = value }

                    FieldLabel { theme: root.theme; text: "FOUNDER SENSORY ACCURACY" }
                    SpinBox { from: 0; to: 100; value: reference.draftSensoryAccuracy; onValueModified: reference.draftSensoryAccuracy = value }
                    FieldLabel { theme: root.theme; text: "EXPLORATION MOVEMENT" }
                    ComboBox {
                        model: ["Moore", "Von Neumann", "Uniform", "Gaussian"]
                        currentIndex: reference.draftExplorationMovement === "von_neumann" ? 1 : reference.draftExplorationMovement === "uniform" ? 2 : reference.draftExplorationMovement === "gaussian" ? 3 : 0
                        onActivated: reference.draftExplorationMovement = ["moore", "von_neumann", "uniform", "gaussian"][currentIndex]
                    }

                    FieldLabel { theme: root.theme; text: "RESOURCE GEOGRAPHY" }
                    ComboBox {
                        model: ["Uniform", "Two patches"]
                        currentIndex: reference.draftResourceGeography === "two_patches" ? 1 : 0
                        onActivated: reference.draftResourceGeography = currentIndex === 1 ? "two_patches" : "uniform"
                    }
                    Item { Layout.columnSpan: 2; Layout.fillWidth: true }
                }

                DisclosureSection {
                    theme: root.theme
                    title: "Advanced supported choices"
                    expanded: false
                    Layout.fillWidth: true
                    contentItem: ColumnLayout {
                        spacing: theme.space3
                        GridLayout {
                            Layout.fillWidth: true
                            columns: 4
                            columnSpacing: theme.space3
                            rowSpacing: theme.space2

                            FieldLabel { theme: root.theme; text: "GAUSSIAN STANDARD DEVIATION"; visible: reference.gaussianApplicable }
                            SpinBox { from: 0; to: 10; value: reference.draftGaussianStandardDeviation; visible: reference.gaussianApplicable; onValueModified: reference.draftGaussianStandardDeviation = value }
                            Item { visible: reference.gaussianApplicable; Layout.fillWidth: true }
                            Item { visible: reference.gaussianApplicable; Layout.fillWidth: true }

                            FieldLabel { theme: root.theme; text: "RENEWABLE RESOURCE AMOUNT" }
                            SpinBox { from: 1; to: 100; value: reference.draftResourceAmount; onValueModified: reference.draftResourceAmount = value }
                            FieldLabel { theme: root.theme; text: "RESOURCE DEPOSITS PER STEP" }
                            SpinBox { from: 1; to: 50; value: reference.draftResourceDeposits; onValueModified: reference.draftResourceDeposits = value }

                            FieldLabel { theme: root.theme; text: "PATCH 1 CENTER X"; visible: reference.patchGeometryApplicable }
                            SpinBox { from: 0; to: 49; value: reference.draftPatch1X; visible: reference.patchGeometryApplicable; onValueModified: reference.draftPatch1X = value }
                            FieldLabel { theme: root.theme; text: "PATCH 1 CENTER Y"; visible: reference.patchGeometryApplicable }
                            SpinBox { from: 0; to: 49; value: reference.draftPatch1Y; visible: reference.patchGeometryApplicable; onValueModified: reference.draftPatch1Y = value }

                            FieldLabel { theme: root.theme; text: "PATCH 1 RADIUS"; visible: reference.patchGeometryApplicable }
                            SpinBox { from: 0; to: 20; value: reference.draftPatch1Radius; visible: reference.patchGeometryApplicable; onValueModified: reference.draftPatch1Radius = value }
                            FieldLabel { theme: root.theme; text: "PATCH 2 CENTER X"; visible: reference.patchGeometryApplicable }
                            SpinBox { from: 0; to: 49; value: reference.draftPatch2X; visible: reference.patchGeometryApplicable; onValueModified: reference.draftPatch2X = value }

                            FieldLabel { theme: root.theme; text: "PATCH 2 CENTER Y"; visible: reference.patchGeometryApplicable }
                            SpinBox { from: 0; to: 49; value: reference.draftPatch2Y; visible: reference.patchGeometryApplicable; onValueModified: reference.draftPatch2Y = value }
                            FieldLabel { theme: root.theme; text: "PATCH 2 RADIUS"; visible: reference.patchGeometryApplicable }
                            SpinBox { from: 0; to: 20; value: reference.draftPatch2Radius; visible: reference.patchGeometryApplicable; onValueModified: reference.draftPatch2Radius = value }

                            FieldLabel { theme: root.theme; text: "MUTATION" }
                            CheckBox { checked: reference.draftMutationEnabled; text: checked ? "Enabled" : "Disabled"; onToggled: reference.draftMutationEnabled = checked }
                            FieldLabel { theme: root.theme; text: "RECOMBINATION PROBABILITY (PPM)" }
                            SpinBox { from: 0; to: 1000000; value: reference.draftRecombinationProbability; onValueModified: reference.draftRecombinationProbability = value }

                            FieldLabel { theme: root.theme; text: "MUTATION PROBABILITY (PPM)"; visible: reference.mutationParametersApplicable }
                            SpinBox { from: 0; to: 100000; value: reference.draftMutationProbability; visible: reference.mutationParametersApplicable; onValueModified: reference.draftMutationProbability = value }
                            FieldLabel { theme: root.theme; text: "MUTATION MAXIMUM CHANGE"; visible: reference.mutationParametersApplicable }
                            SpinBox { from: 1; to: 4; value: reference.draftMutationMaxChange; visible: reference.mutationParametersApplicable; onValueModified: reference.draftMutationMaxChange = value }
                        }
                    }
                }

                DiagnosticBanner {
                    theme: root.theme
                    visible: reference.normalizationNotice
                    tone: "neutral"
                    title: "Inactive parameters reconciled"
                    message: "Values that became scientifically inapplicable were cleared from the transient draft. Saved normalization remains Workbench-owned."
                    Layout.fillWidth: true
                }

                DiagnosticBanner {
                    theme: root.theme
                    visible: reference.readinessMessage.length > 0
                    tone: reference.draftReady ? "neutral" : "warning"
                    title: reference.draftReady ? "Scientific draft ready" : "Scientific draft needs attention"
                    message: reference.readinessMessage
                    Layout.fillWidth: true
                }

                WorkbenchButton {
                    theme: root.theme
                    text: "Save child revision"
                    primary: true
                    enabled: reference.draftDirty && reference.draftReady && !reference.running
                    onClicked: reference.saveChildRevision()
                }
            }
        }

        SurfacePanel {
            theme: root.theme
            visible: app.artifactKind === "b3-flagship" || app.artifactKind === "max-speed-sweep" || app.artifactKind === "environment-selection-comparison"
            Layout.fillWidth: true
            implicitHeight: readOnlyContent.implicitHeight + theme.space4 * 2
            ColumnLayout {
                id: readOnlyContent
                anchors.fill: parent
                anchors.margins: theme.space4
                spacing: theme.space2
                StatusBadge { theme: root.theme; text: app.artifactKind === "b3-flagship" ? "CURATED" : "EXPERIMENT-OWNED FACTOR"; tone: "neutral" }
                Label { text: app.studyTitle; color: theme.text; font.pixelSize: 17; font.weight: Font.DemiBold }
                Label { text: simulation.readOnlyMessage; color: theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                WorkbenchButton {
                    theme: root.theme
                    visible: app.artifactKind === "b3-flagship" && app.canFork
                    text: "Create supported radius-sensitivity fork"
                    enabled: !app.running
                    onClicked: app.forkStudy()
                }
            }
        }

        SurfacePanel {
            theme: root.theme
            Layout.fillWidth: true
            implicitHeight: meaningContent.implicitHeight + theme.space4 * 2
            ColumnLayout {
                id: meaningContent
                anchors.fill: parent
                anchors.margins: theme.space4
                spacing: theme.space3
                Label { text: "Scientific meaning"; color: theme.text; font.pixelSize: 17; font.weight: Font.DemiBold }

                FieldLabel { theme: root.theme; text: "SELECTED / EXPLICIT" }
                Repeater {
                    model: simulation.selectedMeaningModel
                    delegate: Label {
                        required property string label
                        required property string value
                        text: label + ": " + value
                        color: theme.mutedText
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                }

                FieldLabel { theme: root.theme; text: "DERIVED" }
                Repeater {
                    model: simulation.derivedMeaningModel
                    delegate: Label {
                        required property string label
                        required property string value
                        text: label + ": " + value
                        color: theme.mutedText
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                }

                FieldLabel { theme: root.theme; text: "FROZEN ASSUMPTIONS" }
                Repeater {
                    model: simulation.frozenMeaningModel
                    delegate: Label {
                        required property string label
                        required property string value
                        text: label + ": " + value
                        color: theme.subtleText
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                }
            }
        }

        SemanticDiffView {
            theme: root.theme
            diffModel: simulation.semanticDiffModel
            visible: simulation.hasSemanticDiff
            Layout.fillWidth: true
        }
    }
}
