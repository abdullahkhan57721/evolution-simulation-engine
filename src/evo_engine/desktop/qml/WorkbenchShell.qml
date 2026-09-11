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
    readonly property var simulation: applicationController.simulationController
    readonly property var evidence: applicationController.evidenceController
    readonly property var experiment: applicationController.experimentController
    readonly property var run: applicationController.runController
    readonly property var results: applicationController.resultsController

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

    Popup {
        id: runPlanPopup
        modal: true
        focus: true
        closePolicy: Popup.NoAutoClose
        visible: root.run.planOpen
        width: Math.min(root.width - theme.space4 * 2, 920)
        height: Math.min(root.height - theme.space4 * 2, 720)
        x: Math.round((root.width - width) / 2)
        y: Math.round((root.height - height) / 2)
        background: Rectangle {
            color: theme.canvas
            radius: theme.radius
            border.color: theme.border
        }
        contentItem: RunPlanView {
            theme: theme
            run: root.run
        }
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
                            ToolTip.text: "Resolve any blocked scientific draft before opening the exact Run Plan."
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
                    enabled: !root.app.running
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
        SimulationAuthoringView {
            width: sectionLoader.width
            height: sectionLoader.height
            theme: theme
            app: root.app
            reference: root.reference
            simulation: root.simulation
        }
    }

    Component {
        id: evidenceSection
        EvidenceAuthoringView {
            width: sectionLoader.width
            height: sectionLoader.height
            theme: theme
            app: root.app
            evidence: root.evidence
        }
    }

    Component {
        id: experimentSection
        ExperimentAuthoringView {
            width: sectionLoader.width
            height: sectionLoader.height
            theme: theme
            app: root.app
            experiment: root.experiment
        }
    }

    Component {
        id: resultsSection
        ResultsView {
            width: sectionLoader.width
            height: sectionLoader.height
            theme: theme
            app: root.app
            results: root.results
            reference: root.reference
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
