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
        spacing: root.theme.space3

        SectionHeader {
            theme: root.theme
            eyebrow: "Study / Simulation"
            title: "Simulation"
            description: "Edit only the stable semantic choices owned by the active Workbench recipe. Saved changes create immutable child revisions."
            Layout.fillWidth: true
        }

        SurfacePanel {
            theme: root.theme
            visible: root.app.artifactKind === "controlled-run"
            Layout.fillWidth: true
            implicitHeight: controlledContent.implicitHeight + root.theme.space4 * 2
            ColumnLayout {
                id: controlledContent
                anchors.fill: parent
                anchors.margins: root.theme.space4
                spacing: root.theme.space3

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Controlled locomotion"; color: root.theme.text; font.pixelSize: 17; font.weight: Font.DemiBold; Layout.fillWidth: true }
                    StatusBadge { theme: root.theme; text: root.simulation.controlledDraftDirty ? "UNSAVED DRAFT" : "EXACT SAVED REVISION"; tone: root.simulation.controlledDraftDirty ? "warning" : "success" }
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: root.theme.space4
                    rowSpacing: root.theme.space2

                    FieldLabel { theme: root.theme; text: "FOUNDER MAXIMUM SPEED" }
                    SpinBox {
                        from: root.simulation.controlledMinimumMaxSpeed
                        to: root.simulation.controlledMaximumMaxSpeed
                        value: root.simulation.controlledMaxSpeed
                        activeFocusOnTab: true
                        Accessible.name: "Founder maximum speed"
                        onValueModified: root.simulation.controlledMaxSpeed = value
                    }
                    FieldLabel { theme: root.theme; text: "RESOURCE GEOGRAPHY" }
                    ComboBox {
                        model: ["Local resource", "Separated corridor"]
                        currentIndex: root.simulation.controlledResourceGeography === root.simulation.controlledGeographySecondary ? 1 : 0
                        activeFocusOnTab: true
                        Accessible.name: "Resource geography"
                        onActivated: root.simulation.controlledResourceGeography = currentIndex === 1 ? root.simulation.controlledGeographySecondary : root.simulation.controlledGeographyPrimary
                    }
                    FieldLabel { theme: root.theme; text: "RANDOM SEED" }
                    SpinBox {
                        from: -2147483647
                        to: 2147483647
                        value: root.simulation.controlledSeed
                        activeFocusOnTab: true
                        Accessible.name: "Random seed"
                        onValueModified: root.simulation.controlledSeed = value
                    }
                }

                DiagnosticBanner {
                    theme: root.theme
                    visible: root.simulation.controlledReadinessMessage.length > 0
                    tone: root.simulation.controlledDraftReady ? "neutral" : "warning"
                    title: root.simulation.controlledDraftReady ? "Scientific draft ready" : "Scientific draft needs attention"
                    message: root.simulation.controlledReadinessMessage
                    Layout.fillWidth: true
                }

                WorkbenchButton {
                    theme: root.theme
                    text: "Save child revision"
                    primary: true
                    enabled: root.simulation.controlledDraftDirty && root.simulation.controlledDraftReady && !root.app.running
                    onClicked: root.simulation.saveControlledChildRevision()
                }
            }
        }

        SurfacePanel {
            theme: root.theme
            visible: root.app.artifactKind === "reference-ecology"
            Layout.fillWidth: true
            implicitHeight: referenceContent.implicitHeight + root.theme.space4 * 2
            ColumnLayout {
                id: referenceContent
                anchors.fill: parent
                anchors.margins: root.theme.space4
                spacing: root.theme.space3

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: "Reference Ecology · Guided"; color: root.theme.text; font.pixelSize: 17; font.weight: Font.DemiBold; Layout.fillWidth: true }
                    StatusBadge { theme: root.theme; text: root.reference.draftDirty ? "UNSAVED DRAFT" : "EXACT SAVED REVISION"; tone: root.reference.draftDirty ? "warning" : "success" }
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: root.width >= 760 ? 4 : 2
                    columnSpacing: root.theme.space3
                    rowSpacing: root.theme.space2

                    FieldLabel { theme: root.theme; text: "WORLD WIDTH" }
                    SpinBox { from: 4; to: 50; value: root.reference.draftWorldWidth; activeFocusOnTab: true; Accessible.name: "World width"; onValueModified: root.reference.draftWorldWidth = value }
                    FieldLabel { theme: root.theme; text: "WORLD HEIGHT" }
                    SpinBox { from: 4; to: 50; value: root.reference.draftWorldHeight; activeFocusOnTab: true; Accessible.name: "World height"; onValueModified: root.reference.draftWorldHeight = value }

                    FieldLabel { theme: root.theme; text: "FOUNDER POPULATION" }
                    SpinBox { from: 2; to: 100; value: root.reference.draftFounderPopulation; activeFocusOnTab: true; Accessible.name: "Founder population"; onValueModified: root.reference.draftFounderPopulation = value }
                    FieldLabel { theme: root.theme; text: "FOUNDER STARTING ENERGY" }
                    SpinBox { from: 1; to: 200; value: root.reference.draftFounderEnergy; activeFocusOnTab: true; Accessible.name: "Founder starting energy"; onValueModified: root.reference.draftFounderEnergy = value }

                    FieldLabel { theme: root.theme; text: "RUN HORIZON" }
                    SpinBox { from: 1; to: 500; value: root.reference.draftHorizon; activeFocusOnTab: true; Accessible.name: "Run horizon"; onValueModified: root.reference.draftHorizon = value }
                    FieldLabel { theme: root.theme; text: "RANDOM SEED" }
                    SpinBox { from: -2147483647; to: 2147483647; value: root.reference.draftSeed; activeFocusOnTab: true; Accessible.name: "Random seed"; onValueModified: root.reference.draftSeed = value }

                    FieldLabel { theme: root.theme; text: "FOUNDER MAXIMUM SPEED" }
                    SpinBox { from: 0; to: 4; value: root.reference.draftMaxSpeed; activeFocusOnTab: true; Accessible.name: "Founder maximum speed"; onValueModified: root.reference.draftMaxSpeed = value }
                    FieldLabel { theme: root.theme; text: "FOUNDER SENSORY RANGE" }
                    SpinBox { from: 0; to: 20; value: root.reference.draftSensoryRange; activeFocusOnTab: true; Accessible.name: "Founder sensory range"; onValueModified: root.reference.draftSensoryRange = value }

                    FieldLabel { theme: root.theme; text: "FOUNDER SENSORY ACCURACY" }
                    SpinBox { from: 0; to: 100; value: root.reference.draftSensoryAccuracy; activeFocusOnTab: true; Accessible.name: "Founder sensory accuracy"; onValueModified: root.reference.draftSensoryAccuracy = value }
                    FieldLabel { theme: root.theme; text: "EXPLORATION MOVEMENT" }
                    ComboBox {
                        model: ["Moore", "Von Neumann", "Uniform", "Gaussian"]
                        currentIndex: root.reference.draftExplorationMovement === "von_neumann" ? 1 : root.reference.draftExplorationMovement === "uniform" ? 2 : root.reference.draftExplorationMovement === "gaussian" ? 3 : 0
                        activeFocusOnTab: true
                        Accessible.name: "Exploration movement"
                        onActivated: root.reference.draftExplorationMovement = ["moore", "von_neumann", "uniform", "gaussian"][currentIndex]
                    }

                    FieldLabel { theme: root.theme; text: "RESOURCE GEOGRAPHY" }
                    ComboBox {
                        model: ["Uniform", "Two patches"]
                        currentIndex: root.reference.draftResourceGeography === "two_patches" ? 1 : 0
                        activeFocusOnTab: true
                        Accessible.name: "Resource geography"
                        onActivated: root.reference.draftResourceGeography = currentIndex === 1 ? "two_patches" : "uniform"
                    }
                    Item { Layout.columnSpan: 2; Layout.fillWidth: true }
                }

                DisclosureSection {
                    theme: root.theme
                    title: "Advanced supported choices"
                    expanded: false
                    Layout.fillWidth: true
                    contentItem: ColumnLayout {
                        spacing: root.theme.space3
                        GridLayout {
                            Layout.fillWidth: true
                            columns: root.width >= 760 ? 4 : 2
                            columnSpacing: root.theme.space3
                            rowSpacing: root.theme.space2

                            FieldLabel { theme: root.theme; text: "GAUSSIAN STANDARD DEVIATION"; visible: root.reference.gaussianApplicable }
                            SpinBox { from: 0; to: 10; value: root.reference.draftGaussianStandardDeviation; visible: root.reference.gaussianApplicable; activeFocusOnTab: true; Accessible.name: "Gaussian standard deviation"; onValueModified: root.reference.draftGaussianStandardDeviation = value }
                            Item { visible: root.reference.gaussianApplicable && root.width >= 760; Layout.fillWidth: true }
                            Item { visible: root.reference.gaussianApplicable && root.width >= 760; Layout.fillWidth: true }

                            FieldLabel { theme: root.theme; text: "RENEWABLE RESOURCE AMOUNT" }
                            SpinBox { from: 1; to: 100; value: root.reference.draftResourceAmount; activeFocusOnTab: true; Accessible.name: "Renewable resource amount"; onValueModified: root.reference.draftResourceAmount = value }
                            FieldLabel { theme: root.theme; text: "RESOURCE DEPOSITS PER STEP" }
                            SpinBox { from: 1; to: 50; value: root.reference.draftResourceDeposits; activeFocusOnTab: true; Accessible.name: "Resource deposits per step"; onValueModified: root.reference.draftResourceDeposits = value }

                            FieldLabel { theme: root.theme; text: "PATCH 1 CENTER X"; visible: root.reference.patchGeometryApplicable }
                            SpinBox { from: 0; to: 49; value: root.reference.draftPatch1X; visible: root.reference.patchGeometryApplicable; activeFocusOnTab: true; Accessible.name: "Patch 1 center x"; onValueModified: root.reference.draftPatch1X = value }
                            FieldLabel { theme: root.theme; text: "PATCH 1 CENTER Y"; visible: root.reference.patchGeometryApplicable }
                            SpinBox { from: 0; to: 49; value: root.reference.draftPatch1Y; visible: root.reference.patchGeometryApplicable; activeFocusOnTab: true; Accessible.name: "Patch 1 center y"; onValueModified: root.reference.draftPatch1Y = value }

                            FieldLabel { theme: root.theme; text: "PATCH 1 RADIUS"; visible: root.reference.patchGeometryApplicable }
                            SpinBox { from: 0; to: 20; value: root.reference.draftPatch1Radius; visible: root.reference.patchGeometryApplicable; activeFocusOnTab: true; Accessible.name: "Patch 1 radius"; onValueModified: root.reference.draftPatch1Radius = value }
                            FieldLabel { theme: root.theme; text: "PATCH 2 CENTER X"; visible: root.reference.patchGeometryApplicable }
                            SpinBox { from: 0; to: 49; value: root.reference.draftPatch2X; visible: root.reference.patchGeometryApplicable; activeFocusOnTab: true; Accessible.name: "Patch 2 center x"; onValueModified: root.reference.draftPatch2X = value }

                            FieldLabel { theme: root.theme; text: "PATCH 2 CENTER Y"; visible: root.reference.patchGeometryApplicable }
                            SpinBox { from: 0; to: 49; value: root.reference.draftPatch2Y; visible: root.reference.patchGeometryApplicable; activeFocusOnTab: true; Accessible.name: "Patch 2 center y"; onValueModified: root.reference.draftPatch2Y = value }
                            FieldLabel { theme: root.theme; text: "PATCH 2 RADIUS"; visible: root.reference.patchGeometryApplicable }
                            SpinBox { from: 0; to: 20; value: root.reference.draftPatch2Radius; visible: root.reference.patchGeometryApplicable; activeFocusOnTab: true; Accessible.name: "Patch 2 radius"; onValueModified: root.reference.draftPatch2Radius = value }

                            FieldLabel { theme: root.theme; text: "MUTATION" }
                            CheckBox { checked: root.reference.draftMutationEnabled; text: checked ? "Enabled" : "Disabled"; activeFocusOnTab: true; Accessible.name: "Mutation"; onToggled: root.reference.draftMutationEnabled = checked }
                            FieldLabel { theme: root.theme; text: "RECOMBINATION PROBABILITY (PPM)" }
                            SpinBox { from: 0; to: 1000000; value: root.reference.draftRecombinationProbability; activeFocusOnTab: true; Accessible.name: "Recombination probability parts per million"; onValueModified: root.reference.draftRecombinationProbability = value }

                            FieldLabel { theme: root.theme; text: "MUTATION PROBABILITY (PPM)"; visible: root.reference.mutationParametersApplicable }
                            SpinBox { from: 0; to: 100000; value: root.reference.draftMutationProbability; visible: root.reference.mutationParametersApplicable; activeFocusOnTab: true; Accessible.name: "Mutation probability parts per million"; onValueModified: root.reference.draftMutationProbability = value }
                            FieldLabel { theme: root.theme; text: "MUTATION MAXIMUM CHANGE"; visible: root.reference.mutationParametersApplicable }
                            SpinBox { from: 1; to: 4; value: root.reference.draftMutationMaxChange; visible: root.reference.mutationParametersApplicable; activeFocusOnTab: true; Accessible.name: "Mutation maximum change"; onValueModified: root.reference.draftMutationMaxChange = value }
                        }
                    }
                }

                DiagnosticBanner {
                    theme: root.theme
                    visible: root.reference.normalizationNotice
                    tone: "neutral"
                    title: "Inactive parameters reconciled"
                    message: "Values that became scientifically inapplicable were cleared from the transient draft. Saved normalization remains Workbench-owned."
                    Layout.fillWidth: true
                }

                DiagnosticBanner {
                    theme: root.theme
                    visible: root.reference.readinessMessage.length > 0
                    tone: root.reference.draftReady ? "neutral" : "warning"
                    title: root.reference.draftReady ? "Scientific draft ready" : "Scientific draft needs attention"
                    message: root.reference.readinessMessage
                    Layout.fillWidth: true
                }

                WorkbenchButton {
                    theme: root.theme
                    text: "Save child revision"
                    primary: true
                    enabled: root.reference.draftDirty && root.reference.draftReady && !root.reference.running
                    onClicked: root.reference.saveChildRevision()
                }
            }
        }

        SurfacePanel {
            theme: root.theme
            visible: root.app.artifactKind === "b3-flagship" || root.app.artifactKind === "max-speed-sweep" || root.app.artifactKind === "environment-selection-comparison"
            Layout.fillWidth: true
            implicitHeight: readOnlyContent.implicitHeight + root.theme.space4 * 2
            ColumnLayout {
                id: readOnlyContent
                anchors.fill: parent
                anchors.margins: root.theme.space4
                spacing: root.theme.space2
                StatusBadge { theme: root.theme; text: root.app.artifactKind === "b3-flagship" ? "CURATED" : "EXPERIMENT-OWNED FACTOR"; tone: "neutral" }
                Label { text: root.app.studyTitle; color: root.theme.text; font.pixelSize: 17; font.weight: Font.DemiBold; wrapMode: Text.Wrap; Layout.fillWidth: true }
                Label { text: root.simulation.readOnlyMessage; color: root.theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                WorkbenchButton {
                    theme: root.theme
                    visible: root.app.artifactKind === "b3-flagship" && root.app.canFork
                    text: "Create supported radius-sensitivity fork"
                    enabled: !root.app.running
                    onClicked: root.app.forkStudy()
                }
            }
        }

        SurfacePanel {
            theme: root.theme
            Layout.fillWidth: true
            implicitHeight: meaningContent.implicitHeight + root.theme.space4 * 2
            ColumnLayout {
                id: meaningContent
                anchors.fill: parent
                anchors.margins: root.theme.space4
                spacing: root.theme.space3
                Label { text: "Scientific meaning"; color: root.theme.text; font.pixelSize: 17; font.weight: Font.DemiBold }

                FieldLabel { theme: root.theme; text: "SELECTED / EXPLICIT" }
                Repeater {
                    model: root.simulation.selectedMeaningModel
                    delegate: Label {
                        required property string label
                        required property string value
                        text: label + ": " + value
                        color: root.theme.mutedText
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                }

                FieldLabel { theme: root.theme; text: "DERIVED" }
                Repeater {
                    model: root.simulation.derivedMeaningModel
                    delegate: Label {
                        required property string label
                        required property string value
                        text: label + ": " + value
                        color: root.theme.mutedText
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                }

                FieldLabel { theme: root.theme; text: "FROZEN ASSUMPTIONS" }
                Repeater {
                    model: root.simulation.frozenMeaningModel
                    delegate: Label {
                        required property string label
                        required property string value
                        text: label + ": " + value
                        color: root.theme.subtleText
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                }
            }
        }

        SemanticDiffView {
            theme: root.theme
            diffModel: root.simulation.semanticDiffModel
            visible: root.simulation.hasSemanticDiff
            Layout.fillWidth: true
        }
    }
}
