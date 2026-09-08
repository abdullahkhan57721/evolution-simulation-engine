import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 1280
    height: 820
    minimumWidth: 980
    minimumHeight: 680
    visible: true
    title: applicationController.hasStudy
        ? applicationController.studyTitle + " — Evolution Experiment Workbench"
        : "Evolution Experiment Workbench"

    readonly property var app: applicationController
    readonly property var reference: applicationController.referenceController

    WorkbenchTheme { id: theme }

    background: Rectangle { color: theme.canvas }

    Action {
        id: newAction
        text: "New Study"
        shortcut: "Ctrl+N"
        enabled: !root.app.running
        onTriggered: root.app.showNewStudy()
    }
    Action {
        id: openAction
        text: "Open Study…"
        shortcut: "Ctrl+O"
        enabled: !root.app.running
        onTriggered: {
            root.app.showOpenStudy()
            openDialog.open()
        }
    }
    Action {
        id: saveAction
        text: "Save"
        shortcut: "Ctrl+S"
        enabled: root.app.hasStudy && !root.app.running
        onTriggered: {
            if (root.app.hasFileLocation)
                root.app.saveToCurrentLocation()
            else
                saveDialog.open()
        }
    }
    Action {
        id: saveAsAction
        text: "Save As…"
        shortcut: "Ctrl+Shift+S"
        enabled: root.app.hasStudy && !root.app.running
        onTriggered: saveDialog.open()
    }

    menuBar: MenuBar {
        Menu {
            title: "File"
            MenuItem { action: newAction }
            MenuItem { action: openAction }
            MenuSeparator {}
            MenuItem { action: saveAction }
            MenuItem { action: saveAsAction }
            MenuSeparator {}
            MenuItem {
                text: "Return Home"
                enabled: root.app.route !== "home" && !root.app.running
                onTriggered: root.app.goHome()
            }
        }
    }

    FileDialog {
        id: openDialog
        title: "Open Workbench Study"
        fileMode: FileDialog.OpenFile
        nameFilters: ["Workbench Study (*.json)", "JSON files (*.json)"]
        onAccepted: root.app.openStudy(selectedFile.toString())
    }

    FileDialog {
        id: saveDialog
        title: "Save exact Workbench artifact"
        fileMode: FileDialog.SaveFile
        defaultSuffix: "json"
        nameFilters: ["Workbench Study (*.json)"]
        onAccepted: root.app.saveStudy(selectedFile.toString())
    }

    header: Rectangle {
        implicitHeight: 62
        color: theme.canvasRaised
        border.color: theme.border

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: theme.space4
            anchors.rightMargin: theme.space4
            spacing: theme.space3

            Rectangle {
                width: 28
                height: 28
                radius: 8
                color: theme.accent
                Label {
                    anchors.centerIn: parent
                    text: "E"
                    color: theme.accentText
                    font.bold: true
                    font.pixelSize: 15
                }
            }
            ColumnLayout {
                spacing: 1
                Layout.fillWidth: true
                Label {
                    text: "Evolution Experiment Workbench"
                    color: theme.text
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                }
                Label {
                    text: root.app.route === "study"
                        ? root.app.studyTitle + " · " + root.app.studySection
                        : root.app.route === "new"
                            ? "New Study"
                            : root.app.route === "open"
                                ? "Open Study"
                                : "Computational evolutionary-biology laboratory"
                    color: theme.mutedText
                    font.pixelSize: theme.textSmall
                }
            }
            StatusBadge {
                theme: theme
                visible: root.app.hasStudy
                text: root.app.readinessState.length > 0
                    ? root.app.readinessState.toUpperCase()
                    : ""
                tone: root.app.readinessState === "ready"
                    ? "success"
                    : root.app.readinessState === "blocked"
                        ? "error"
                        : "warning"
            }
        }
    }

    Loader {
        id: routeLoader
        anchors.fill: parent
        sourceComponent: root.app.route === "study"
            ? studyRoute
            : root.app.route === "new"
                ? newRoute
                : root.app.route === "open"
                    ? openRoute
                    : homeRoute
    }

    Component {
        id: homeRoute
        ScrollView {
            contentWidth: availableWidth
            clip: true

            ColumnLayout {
                width: Math.max(760, routeLoader.width - theme.space5 * 2)
                x: Math.max(theme.space5, (routeLoader.width - width) / 2)
                spacing: theme.space4

                Item { Layout.preferredHeight: theme.space3 }

                SectionHeader {
                    theme: theme
                    eyebrow: "Native Workbench"
                    title: "Build, run, inspect, and present reproducible evolutionary studies."
                    description: "Scientific meaning stays in the existing Workbench. The desktop shell owns navigation, exact files, and transient application state."
                    Layout.fillWidth: true
                }

                RowLayout {
                    spacing: theme.space3
                    WorkbenchButton {
                        theme: theme
                        primary: true
                        text: "New Study"
                        onClicked: root.app.showNewStudy()
                    }
                    WorkbenchButton {
                        theme: theme
                        text: "Open Study…"
                        onClicked: {
                            root.app.showOpenStudy()
                            openDialog.open()
                        }
                    }
                }

                Label {
                    text: "SUPPORTED STUDY FAMILIES"
                    color: theme.subtleText
                    font.pixelSize: theme.textSmall
                    font.weight: Font.DemiBold
                    font.letterSpacing: 0.7
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: routeLoader.width >= 1080 ? 3 : 1
                    columnSpacing: theme.space3
                    rowSpacing: theme.space3

                    SurfacePanel {
                        theme: theme
                        Layout.fillWidth: true
                        Layout.preferredHeight: 150
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: theme.space3
                            spacing: theme.space2
                            StatusBadge { theme: theme; text: "CURATED"; tone: "neutral" }
                            Label { text: "B3 Flagship"; color: theme.text; font.pixelSize: theme.textTitle; font.weight: Font.DemiBold }
                            Label { text: "Canonical confirmed radius-1 selection study."; color: theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                            Item { Layout.fillHeight: true }
                        }
                    }
                    SurfacePanel {
                        theme: theme
                        Layout.fillWidth: true
                        Layout.preferredHeight: 150
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: theme.space3
                            spacing: theme.space2
                            StatusBadge { theme: theme; text: "CONTROLLED"; tone: "neutral" }
                            Label { text: "Locomotion experiments"; color: theme.text; font.pixelSize: theme.textTitle; font.weight: Font.DemiBold }
                            Label { text: "Single run · max-speed sweep · environment comparison."; color: theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                            Item { Layout.fillHeight: true }
                        }
                    }
                    SurfacePanel {
                        theme: theme
                        Layout.fillWidth: true
                        Layout.preferredHeight: 150
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: theme.space3
                            spacing: theme.space2
                            StatusBadge { theme: theme; text: "CUSTOM"; tone: "neutral" }
                            Label { text: "Reference Ecology"; color: theme.text; font.pixelSize: theme.textTitle; font.weight: Font.DemiBold }
                            Label { text: "Bounded Workbench-supported ecological composition."; color: theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                            Item { Layout.fillHeight: true }
                        }
                    }
                }

                DiagnosticBanner {
                    theme: theme
                    tone: root.app.statusTone
                    title: "Application status"
                    message: root.app.status
                    visible: root.app.status.length > 0
                    Layout.fillWidth: true
                }
            }
        }
    }

    Component {
        id: newRoute
        ScrollView {
            contentWidth: availableWidth
            clip: true
            ColumnLayout {
                width: Math.max(760, routeLoader.width - theme.space5 * 2)
                x: Math.max(theme.space5, (routeLoader.width - width) / 2)
                spacing: theme.space4

                Item { Layout.preferredHeight: theme.space3 }
                RowLayout {
                    Layout.fillWidth: true
                    WorkbenchButton { theme: theme; text: "← Home"; onClicked: root.app.goHome() }
                    Item { Layout.fillWidth: true }
                }
                SectionHeader {
                    theme: theme
                    eyebrow: "New Study"
                    title: "Choose a supported scientific workflow"
                    description: "Each choice creates an existing concrete Workbench artifact. Q1 does not wrap them in a universal Study format."
                    Layout.fillWidth: true
                }

                Label { text: "CURATED"; color: theme.subtleText; font.pixelSize: theme.textSmall; font.weight: Font.DemiBold }
                SurfacePanel {
                    theme: theme
                    Layout.fillWidth: true
                    implicitHeight: b3NewContent.implicitHeight + theme.space4 * 2
                    RowLayout {
                        id: b3NewContent
                        anchors.fill: parent
                        anchors.margins: theme.space4
                        spacing: theme.space3
                        ColumnLayout {
                            Layout.fillWidth: true
                            Label { text: "B3 Flagship"; color: theme.text; font.pixelSize: theme.textTitle; font.weight: Font.DemiBold }
                            Label { text: "Start from the canonical validated radius-1 B3 scientific definition."; color: theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                        }
                        WorkbenchButton { theme: theme; primary: true; text: "Start"; onClicked: root.app.createStudy("b3-flagship") }
                    }
                }

                Label { text: "CONTROLLED"; color: theme.subtleText; font.pixelSize: theme.textSmall; font.weight: Font.DemiBold }
                GridLayout {
                    Layout.fillWidth: true
                    columns: routeLoader.width >= 1120 ? 3 : 1
                    columnSpacing: theme.space3
                    rowSpacing: theme.space3

                    SurfacePanel {
                        theme: theme
                        Layout.fillWidth: true
                        implicitHeight: 170
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: theme.space3
                            spacing: theme.space2
                            Label { text: "Single controlled run"; color: theme.text; font.pixelSize: 17; font.weight: Font.DemiBold }
                            Label { text: "One bounded controlled-locomotion Study revision."; color: theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                            Item { Layout.fillHeight: true }
                            WorkbenchButton { theme: theme; text: "Start controlled run"; Layout.fillWidth: true; onClicked: root.app.createStudy("controlled-run") }
                        }
                    }
                    SurfacePanel {
                        theme: theme
                        Layout.fillWidth: true
                        implicitHeight: 170
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: theme.space3
                            spacing: theme.space2
                            Label { text: "Max-speed sweep"; color: theme.text; font.pixelSize: 17; font.weight: Font.DemiBold }
                            Label { text: "Existing E3-pattern maximum-speed factor sweep."; color: theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                            Item { Layout.fillHeight: true }
                            WorkbenchButton { theme: theme; text: "Start max-speed sweep"; Layout.fillWidth: true; onClicked: root.app.createStudy("max-speed-sweep") }
                        }
                    }
                    SurfacePanel {
                        theme: theme
                        Layout.fillWidth: true
                        implicitHeight: 170
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: theme.space3
                            spacing: theme.space2
                            Label { text: "Environment comparison"; color: theme.text; font.pixelSize: 17; font.weight: Font.DemiBold }
                            Label { text: "Existing E4 matched environment-selection comparison."; color: theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                            Item { Layout.fillHeight: true }
                            WorkbenchButton { theme: theme; text: "Start environment comparison"; Layout.fillWidth: true; onClicked: root.app.createStudy("environment-selection-comparison") }
                        }
                    }
                }

                Label { text: "CUSTOM"; color: theme.subtleText; font.pixelSize: theme.textSmall; font.weight: Font.DemiBold }
                SurfacePanel {
                    theme: theme
                    Layout.fillWidth: true
                    implicitHeight: referenceNewContent.implicitHeight + theme.space4 * 2
                    RowLayout {
                        id: referenceNewContent
                        anchors.fill: parent
                        anchors.margins: theme.space4
                        spacing: theme.space3
                        ColumnLayout {
                            Layout.fillWidth: true
                            Label { text: "Reference Ecology"; color: theme.text; font.pixelSize: theme.textTitle; font.weight: Font.DemiBold }
                            Label { text: "Start the bounded WB4 recipe. Extension/internal engine capabilities remain outside ordinary authoring."; color: theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                        }
                        WorkbenchButton { theme: theme; primary: true; text: "Start"; onClicked: root.app.createStudy("reference-ecology") }
                    }
                }
            }
        }
    }

    Component {
        id: openRoute
        Item {
            ColumnLayout {
                anchors.centerIn: parent
                width: Math.min(680, parent.width - theme.space5 * 2)
                spacing: theme.space3

                WorkbenchButton { theme: theme; text: "← Home"; onClicked: root.app.goHome() }
                SurfacePanel {
                    theme: theme
                    Layout.fillWidth: true
                    implicitHeight: openContent.implicitHeight + theme.space5 * 2
                    ColumnLayout {
                        id: openContent
                        anchors.fill: parent
                        anchors.margins: theme.space5
                        spacing: theme.space3
                        SectionHeader {
                            theme: theme
                            eyebrow: "Open Study"
                            title: "Open an exact Workbench artifact"
                            description: "The native shell dispatches by existing format and pattern identity, then calls the concrete loader. Historical manifests are never re-resolved."
                            Layout.fillWidth: true
                        }
                        WorkbenchButton {
                            theme: theme
                            primary: true
                            text: "Choose JSON file…"
                            Layout.alignment: Qt.AlignLeft
                            onClicked: openDialog.open()
                        }
                    }
                }
                DiagnosticBanner {
                    theme: theme
                    visible: root.app.diagnosticMessage.length > 0 || root.app.statusTone === "error"
                    tone: "error"
                    title: root.app.diagnosticMessage.length > 0 ? "Exact reproduction unavailable" : "Open failed"
                    message: root.app.diagnosticMessage.length > 0 ? root.app.diagnosticMessage : root.app.status
                    remediation: root.app.diagnosticRemediation
                    Layout.fillWidth: true
                }
            }
        }
    }

    Component {
        id: studyRoute
        RowLayout {
            anchors.fill: parent
            anchors.margins: theme.space3
            spacing: theme.space3

            SurfacePanel {
                theme: theme
                Layout.preferredWidth: 218
                Layout.fillHeight: true
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: theme.space3
                    spacing: theme.space2

                    WorkbenchButton {
                        theme: theme
                        text: "← Home"
                        enabled: !root.app.running
                        Layout.fillWidth: true
                        onClicked: root.app.goHome()
                    }
                    Item { Layout.preferredHeight: theme.space2 }
                    Label { text: "STUDY"; color: theme.subtleText; font.pixelSize: theme.textSmall; font.weight: Font.DemiBold; font.letterSpacing: 0.7 }
                    SidebarButton { theme: theme; text: "Simulation"; selected: root.app.studySection === "Simulation"; Layout.fillWidth: true; onClicked: root.app.selectSection("Simulation") }
                    SidebarButton { theme: theme; text: "Evidence"; selected: root.app.studySection === "Evidence"; Layout.fillWidth: true; onClicked: root.app.selectSection("Evidence") }
                    SidebarButton { theme: theme; text: "Experiment"; selected: root.app.studySection === "Experiment"; Layout.fillWidth: true; onClicked: root.app.selectSection("Experiment") }
                    SidebarButton { theme: theme; text: "Results"; selected: root.app.studySection === "Results"; Layout.fillWidth: true; onClicked: root.app.selectSection("Results") }
                    SidebarButton { theme: theme; text: "Presentation"; selected: root.app.studySection === "Presentation"; Layout.fillWidth: true; onClicked: root.app.selectSection("Presentation") }
                    Item { Layout.fillHeight: true }
                    Label {
                        text: root.app.fileLocation.length > 0 ? "Saved file\n" + root.app.fileLocation : "No file location yet"
                        color: theme.subtleText
                        font.pixelSize: theme.textSmall
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: theme.space3

                SurfacePanel {
                    theme: theme
                    Layout.fillWidth: true
                    implicitHeight: studyHeaderContent.implicitHeight + theme.space3 * 2
                    RowLayout {
                        id: studyHeaderContent
                        anchors.fill: parent
                        anchors.margins: theme.space3
                        spacing: theme.space3

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: theme.space1
                            Label { text: root.app.studyTitle; color: theme.text; font.pixelSize: theme.textTitle; font.weight: Font.DemiBold }
                            Label { text: root.app.studyTypeLabel; color: theme.mutedText; font.pixelSize: theme.textSmall }
                            RowLayout {
                                spacing: theme.space2
                                StatusBadge {
                                    theme: theme
                                    visible: root.app.revisionId.length > 0
                                    text: "REV " + root.app.revisionId
                                    tone: "neutral"
                                }
                                StatusBadge {
                                    theme: theme
                                    text: root.app.readinessState.toUpperCase()
                                    tone: root.app.readinessState === "ready" ? "success" : root.app.readinessState === "blocked" ? "error" : "warning"
                                }
                                StatusBadge {
                                    theme: theme
                                    visible: root.app.scenarioIdentity.length > 0
                                    text: "VALIDATED SCENARIO"
                                    tone: "success"
                                }
                            }
                        }

                        WorkbenchButton {
                            theme: theme
                            text: "Fork"
                            visible: root.app.canFork
                            enabled: root.app.canFork && !root.app.running
                            onClicked: root.app.forkStudy()
                        }
                        WorkbenchButton {
                            theme: theme
                            text: root.app.hasFileLocation ? "Save" : "Save As…"
                            enabled: !root.app.running
                            onClicked: {
                                if (root.app.hasFileLocation)
                                    root.app.saveToCurrentLocation()
                                else
                                    saveDialog.open()
                            }
                        }
                        WorkbenchButton {
                            theme: theme
                            text: "Save As…"
                            enabled: !root.app.running
                            onClicked: saveDialog.open()
                        }
                        WorkbenchButton {
                            theme: theme
                            primary: true
                            text: root.app.running ? "Running…" : "Run"
                            enabled: root.app.canRun
                            onClicked: root.app.runStudy()
                            ToolTip.visible: hovered && !enabled
                            ToolTip.text: root.app.artifactKind === "reference-ecology"
                                ? "Save any Reference draft before running."
                                : "Native execution for this family arrives in a later Q milestone."
                        }
                    }
                }

                DiagnosticBanner {
                    theme: theme
                    visible: root.app.diagnosticMessage.length > 0
                    tone: "error"
                    title: "Exact reproduction unavailable"
                    message: root.app.diagnosticMessage
                    remediation: root.app.diagnosticRemediation
                    Layout.fillWidth: true
                }

                Loader {
                    id: sectionLoader
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    sourceComponent: root.app.studySection === "Simulation"
                        ? simulationSection
                        : root.app.studySection === "Evidence"
                            ? evidenceSection
                            : root.app.studySection === "Experiment"
                                ? experimentSection
                                : root.app.studySection === "Results"
                                    ? resultsSection
                                    : presentationSection
                }

                Label {
                    Layout.fillWidth: true
                    text: root.app.status
                    color: root.app.statusTone === "error"
                        ? theme.danger
                        : root.app.statusTone === "warning"
                            ? theme.warning
                            : root.app.statusTone === "success"
                                ? theme.success
                                : theme.mutedText
                    font.pixelSize: theme.textSmall
                    wrapMode: Text.Wrap
                }
            }
        }
    }

    Component {
        id: simulationSection
        ScrollView {
            contentWidth: availableWidth
            clip: true
            ColumnLayout {
                width: sectionLoader.width
                spacing: theme.space3
                SectionHeader {
                    theme: theme
                    eyebrow: "Study / Simulation"
                    title: "Simulation"
                    description: root.app.artifactKind === "reference-ecology"
                        ? "Q1 retains the proven Reference Ecology semantic edit without expanding full native authoring."
                        : "The shell preserves this Study family's exact scientific owner. Full native Simulation authoring arrives later."
                    Layout.fillWidth: true
                }

                SurfacePanel {
                    theme: theme
                    Layout.fillWidth: true
                    implicitHeight: simulationContent.implicitHeight + theme.space4 * 2
                    ColumnLayout {
                        id: simulationContent
                        anchors.fill: parent
                        anchors.margins: theme.space4
                        spacing: theme.space3

                        ColumnLayout {
                            visible: root.app.artifactKind === "reference-ecology"
                            Layout.fillWidth: true
                            spacing: theme.space3
                            FieldLabel { theme: theme; text: "FOUNDER MAXIMUM SPEED" }
                            RowLayout {
                                Layout.fillWidth: true
                                SpinBox {
                                    from: 0
                                    to: 4
                                    value: root.reference.draftMaxSpeed
                                    enabled: root.reference.active && !root.reference.running
                                    onValueModified: root.reference.draftMaxSpeed = value
                                }
                                StatusBadge {
                                    theme: theme
                                    text: root.reference.draftDirty ? "UNSAVED DRAFT" : "EXACT SAVED REVISION"
                                    tone: root.reference.draftDirty ? "warning" : "success"
                                }
                                Item { Layout.fillWidth: true }
                                WorkbenchButton {
                                    theme: theme
                                    text: "Save child revision"
                                    enabled: root.reference.draftDirty && root.reference.draftReady && !root.reference.running
                                    onClicked: root.reference.saveChildRevision()
                                }
                            }
                            FieldLabel { theme: theme; text: "EXPLICIT MEANING" }
                            Label { text: root.reference.explicitMeaning; color: theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                            FieldLabel { theme: theme; text: "DERIVED MEANING" }
                            Label { text: root.reference.derivedMeaning; color: theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                        }

                        ColumnLayout {
                            visible: root.app.artifactKind !== "reference-ecology"
                            Layout.fillWidth: true
                            spacing: theme.space2
                            Label { text: root.app.studyTitle + " scientific definition"; color: theme.text; font.pixelSize: 17; font.weight: Font.DemiBold }
                            Label { text: "Q1 displays identity and readiness only. Navigation cannot mutate this concrete artifact."; color: theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                        }
                    }
                }

                DisclosureSection {
                    theme: theme
                    title: "Exact scientific identity"
                    expanded: false
                    Layout.fillWidth: true
                    contentItem: [
                        Label { text: root.app.revisionId.length > 0 ? "Revision: " + root.app.revisionId : "Revision identity: not owned by this artifact type"; color: theme.mutedText },
                        Label { text: root.app.parentRevisionId.length > 0 ? "Parent revision: " + root.app.parentRevisionId : "Parent revision: —"; color: theme.mutedText },
                        Label { text: root.app.manifestDigest.length > 0 ? "Manifest: " + root.app.manifestDigest : "Manifest digest: owned inside experiment treatments when applicable"; color: theme.mutedText; wrapMode: Text.Wrap },
                        Label { visible: root.app.scenarioOrigin.length > 0; text: "Scenario origin: " + root.app.scenarioOrigin; color: theme.mutedText },
                        Label { visible: root.app.artifactKind === "b3-flagship"; text: "Validated scenario identity: " + (root.app.scenarioIdentity.length > 0 ? root.app.scenarioIdentity : "not retained by this B3-derived fork"); color: theme.mutedText; wrapMode: Text.Wrap }
                    ]
                }
            }
        }
    }

    Component {
        id: evidenceSection
        ScrollView {
            contentWidth: availableWidth
            ColumnLayout {
                width: sectionLoader.width
                spacing: theme.space3
                SectionHeader {
                    theme: theme
                    eyebrow: "Study / Evidence"
                    title: "Evidence"
                    description: "Q1 preserves the exact evidence plan already stored by the active concrete artifact. Evidence authoring is a later native milestone."
                    Layout.fillWidth: true
                }
                SurfacePanel {
                    theme: theme
                    Layout.fillWidth: true
                    implicitHeight: 170
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: theme.space4
                        spacing: theme.space2
                        StatusBadge { theme: theme; text: "EXACT PERSISTED MEANING"; tone: "success" }
                        Label { text: "No Q1 Evidence editor"; color: theme.text; font.pixelSize: 17; font.weight: Font.DemiBold }
                        Label { text: "Opening, saving, and changing sections never synthesize or re-resolve evidence. Q3 can build family-specific Evidence controls over the settled application-state seam."; color: theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                    }
                }
            }
        }
    }

    Component {
        id: experimentSection
        ScrollView {
            contentWidth: availableWidth
            ColumnLayout {
                width: sectionLoader.width
                spacing: theme.space3
                SectionHeader {
                    theme: theme
                    eyebrow: "Study / Experiment"
                    title: "Experiment"
                    description: "Concrete experiment identity remains separate from ordinary Simulation authoring. Q1 does not introduce a generic experiment editor."
                    Layout.fillWidth: true
                }
                SurfacePanel {
                    theme: theme
                    Layout.fillWidth: true
                    implicitHeight: 180
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: theme.space4
                        spacing: theme.space2
                        StatusBadge {
                            theme: theme
                            text: root.app.artifactKind === "max-speed-sweep" || root.app.artifactKind === "environment-selection-comparison" ? "EXPERIMENT DEFINITION" : "STUDY WORKFLOW"
                            tone: "neutral"
                        }
                        Label { text: root.app.studyTitle; color: theme.text; font.pixelSize: 17; font.weight: Font.DemiBold }
                        Label {
                            text: root.app.artifactKind === "max-speed-sweep"
                                ? "Maximum speed remains the existing E3 semantic factor; seeds remain replicate design."
                                : root.app.artifactKind === "environment-selection-comparison"
                                    ? "Resource geography remains the E4 factor; control/treatment and standing composition stay frozen."
                                    : "This Study family has no Q1 experiment-editing surface."
                            color: theme.mutedText
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }
    }

    Component {
        id: resultsSection
        ScrollView {
            contentWidth: availableWidth
            ColumnLayout {
                width: sectionLoader.width
                spacing: theme.space3
                SectionHeader {
                    theme: theme
                    eyebrow: "Study / Results"
                    title: "Results"
                    description: "Q1 binds only current-session results that existing Workbench/WB5 ownership semantics accept for the active scientific artifact."
                    Layout.fillWidth: true
                }

                SurfacePanel {
                    theme: theme
                    Layout.fillWidth: true
                    implicitHeight: resultsContent.implicitHeight + theme.space4 * 2
                    ColumnLayout {
                        id: resultsContent
                        anchors.fill: parent
                        anchors.margins: theme.space4
                        spacing: theme.space3

                        RowLayout {
                            Layout.fillWidth: true
                            Label {
                                text: root.app.hasResult ? "Current authoritative result" : "No current-session result"
                                color: theme.text
                                font.pixelSize: 17
                                font.weight: Font.DemiBold
                                Layout.fillWidth: true
                            }
                            StatusBadge {
                                theme: theme
                                text: root.app.hasResult ? "OWNER MATCHED" : "NO SESSION RESULT"
                                tone: root.app.hasResult ? "success" : "neutral"
                            }
                        }
                        Label {
                            text: root.app.artifactKind === "reference-ecology" && root.reference.hasResult
                                ? "Final population: " + root.reference.finalPopulation
                                : root.app.hasResult
                                    ? "The result is bound to this exact active scientific owner. Family-specific Results parity arrives later."
                                    : "Saved run references may remain in the artifact, but Q1 does not reconstruct or rerun historical result payloads."
                            color: theme.mutedText
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                        }
                    }
                }

                SurfacePanel {
                    theme: theme
                    visible: root.app.artifactKind === "reference-ecology" && root.reference.hasWorld
                    Layout.fillWidth: true
                    Layout.preferredHeight: 390
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: theme.space3
                        spacing: theme.space2
                        RowLayout {
                            Layout.fillWidth: true
                            Label { text: "Recorded world"; color: theme.text; font.pixelSize: 17; font.weight: Font.DemiBold; Layout.fillWidth: true }
                            StatusBadge { theme: theme; text: "COMMITTED STEP " + root.reference.worldStep; tone: "neutral" }
                        }
                        Rectangle {
                            id: resultsWorldCanvas
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: theme.canvasRaised
                            radius: theme.radius
                            border.color: theme.border
                            clip: true

                            Repeater {
                                model: root.reference.resourceModel
                                delegate: Rectangle {
                                    width: Math.max(3, Math.min(10, 2 + amount / 4))
                                    height: width
                                    radius: width / 2
                                    color: theme.resource
                                    opacity: 0.55
                                    x: (worldX + 0.5) / Math.max(1, root.reference.worldWidth) * resultsWorldCanvas.width - width / 2
                                    y: (worldY + 0.5) / Math.max(1, root.reference.worldHeight) * resultsWorldCanvas.height - height / 2
                                }
                            }
                            Repeater {
                                model: root.reference.organismModel
                                delegate: Rectangle {
                                    width: markerSize
                                    height: markerSize
                                    radius: width / 2
                                    color: selected ? theme.selected : theme.organism
                                    border.width: selected ? 3 : 1
                                    border.color: selected ? theme.warning : theme.text
                                    x: (worldX + 0.5) / Math.max(1, root.reference.worldWidth) * resultsWorldCanvas.width - width / 2
                                    y: (worldY + 0.5) / Math.max(1, root.reference.worldHeight) * resultsWorldCanvas.height - height / 2
                                    ToolTip.visible: hover.hovered
                                    ToolTip.text: "Organism " + organismId + " · mass " + bodyMass + " · energy " + energy
                                    HoverHandler { id: hover }
                                    TapHandler { onTapped: root.reference.selectOrganism(organismId) }
                                }
                            }
                        }
                    }
                }

                DiagnosticBanner {
                    theme: theme
                    visible: root.app.artifactKind === "reference-ecology" && root.reference.hasResult && !root.reference.hasWorld
                    tone: "neutral"
                    title: "No recorded spatial replay in this exact result"
                    message: "Q1 does not reconstruct unrecorded world state. A Reference result can render natively only when its exact EvidencePlan recorded spatial evidence."
                    Layout.fillWidth: true
                }
            }
        }
    }

    Component {
        id: presentationSection
        ScrollView {
            contentWidth: availableWidth
            ColumnLayout {
                width: sectionLoader.width
                spacing: theme.space3
                SectionHeader {
                    theme: theme
                    eyebrow: "Study / Presentation"
                    title: "Presentation"
                    description: "Presentation remains downstream of exact recorded evidence. Q1 establishes ownership/reset semantics; broader world exploration and B3 presentation parity arrive later."
                    Layout.fillWidth: true
                }
                SurfacePanel {
                    theme: theme
                    Layout.fillWidth: true
                    implicitHeight: 190
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: theme.space4
                        spacing: theme.space2
                        StatusBadge {
                            theme: theme
                            text: root.app.presentationOwner.length > 0 ? "EXACT RESULT OWNER" : "NO PRESENTATION OWNER"
                            tone: root.app.presentationOwner.length > 0 ? "success" : "neutral"
                        }
                        Label { text: "Presentation state epoch " + root.app.presentationEpoch; color: theme.text; font.pixelSize: 17; font.weight: Font.DemiBold }
                        Label {
                            text: root.app.presentationOwner.length > 0
                                ? "Presentation state is scoped to the exact active revision / manifest / run owner. Changing scientific ownership resets it."
                                : "No exact current-session result is bound for presentation. Historical references alone are never converted into replay data."
                            color: theme.mutedText
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }
    }
}
