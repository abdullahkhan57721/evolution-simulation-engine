import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 1280
    height: 820
    minimumWidth: 1024
    minimumHeight: 700
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
    readonly property var presentation: presentationController

    WorkbenchTheme { id: theme }
    readonly property var uiTheme: theme

    background: Rectangle { color: root.uiTheme.canvas }

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
        Accessible.name: "Application menu"
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
        objectName: "runPlanPopup"
        modal: true
        focus: true
        closePolicy: Popup.NoAutoClose
        visible: root.run.planOpen
        width: Math.min(root.width - root.uiTheme.space4 * 2, 920)
        height: Math.min(root.height - root.uiTheme.space4 * 2, 720)
        x: Math.round((root.width - width) / 2)
        y: Math.round((root.height - height) / 2)
        background: Rectangle {
            color: root.uiTheme.canvas
            radius: root.uiTheme.radius
            border.color: root.uiTheme.border
        }
        contentItem: RunPlanView {
            theme: root.uiTheme
            run: root.run
            Accessible.name: "Exact Run Plan"
        }
        onOpened: Qt.callLater(function() {
            if (contentItem)
                contentItem.forceActiveFocus(Qt.TabFocusReason)
        })
    }

    header: Rectangle {
        implicitHeight: 62
        color: root.uiTheme.canvasRaised
        border.color: root.uiTheme.border

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: root.uiTheme.space4
            anchors.rightMargin: root.uiTheme.space4
            spacing: root.uiTheme.space3

            Rectangle {
                width: 28
                height: 28
                radius: 8
                color: root.uiTheme.accent
                Accessible.ignored: true
                Label {
                    anchors.centerIn: parent
                    text: "E"
                    color: root.uiTheme.accentText
                    font.bold: true
                    font.pixelSize: 15
                }
            }
            ColumnLayout {
                spacing: 1
                Layout.fillWidth: true
                Label {
                    text: "Evolution Experiment Workbench"
                    color: root.uiTheme.text
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
                Label {
                    text: root.app.route === "study"
                        ? root.app.studyTitle + " · " + root.app.studySection
                        : root.app.route === "new"
                            ? "New Study"
                            : root.app.route === "open"
                                ? "Open Study"
                                : "Computational evolutionary-biology laboratory"
                    color: root.uiTheme.mutedText
                    font.pixelSize: root.uiTheme.textSmall
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
            }
            StatusBadge {
                theme: root.uiTheme
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
        objectName: "routeLoader"
        anchors.fill: parent
        focus: true
        sourceComponent: root.app.route === "study"
            ? studyRoute
            : root.app.route === "new"
                ? newRoute
                : root.app.route === "open"
                    ? openRoute
                    : homeRoute
        onLoaded: Qt.callLater(function() {
            if (item)
                item.forceActiveFocus(Qt.TabFocusReason)
        })
    }

    Component {
        id: homeRoute
        FocusScope {
            id: homeScope
            objectName: "homeRoute"

            ScrollView {
                anchors.fill: parent
                contentWidth: availableWidth
                clip: true

                ColumnLayout {
                    width: Math.min(1180, Math.max(0, homeScope.width - root.uiTheme.space5 * 2))
                    x: Math.max(root.uiTheme.space5, Math.round((homeScope.width - width) / 2))
                    spacing: root.uiTheme.space4

                    Item { Layout.preferredHeight: root.uiTheme.space3 }

                    SectionHeader {
                        theme: root.uiTheme
                        eyebrow: "Native Workbench"
                        title: "Build, run, inspect, and present reproducible evolutionary studies."
                        description: "Scientific meaning stays in the existing Workbench. The desktop shell owns navigation, exact files, and transient application state."
                        Layout.fillWidth: true
                    }

                    RowLayout {
                        spacing: root.uiTheme.space3
                        WorkbenchButton {
                            id: homeNewButton
                            objectName: "homeNewStudy"
                            theme: root.uiTheme
                            primary: true
                            text: "New Study"
                            KeyNavigation.right: homeOpenButton
                            KeyNavigation.tab: homeOpenButton
                            onClicked: root.app.showNewStudy()
                        }
                        WorkbenchButton {
                            id: homeOpenButton
                            objectName: "homeOpenStudy"
                            theme: root.uiTheme
                            text: "Open Study…"
                            KeyNavigation.left: homeNewButton
                            onClicked: {
                                root.app.showOpenStudy()
                                openDialog.open()
                            }
                        }
                    }

                    Label {
                        text: "SUPPORTED STUDY FAMILIES"
                        color: root.uiTheme.subtleText
                        font.pixelSize: root.uiTheme.textSmall
                        font.weight: Font.DemiBold
                        font.letterSpacing: 0.7
                    }

                    GridLayout {
                        Layout.fillWidth: true
                        columns: homeScope.width >= 1080 ? 3 : 1
                        columnSpacing: root.uiTheme.space3
                        rowSpacing: root.uiTheme.space3

                        SurfacePanel {
                            theme: root.uiTheme
                            Layout.fillWidth: true
                            Layout.preferredHeight: 150
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: root.uiTheme.space3
                                spacing: root.uiTheme.space2
                                StatusBadge { theme: root.uiTheme; text: "CURATED"; tone: "neutral" }
                                Label { text: "B3 Flagship"; color: root.uiTheme.text; font.pixelSize: root.uiTheme.textTitle; font.weight: Font.DemiBold }
                                Label { text: "Canonical confirmed radius-1 selection study."; color: root.uiTheme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                                Item { Layout.fillHeight: true }
                            }
                        }
                        SurfacePanel {
                            theme: root.uiTheme
                            Layout.fillWidth: true
                            Layout.preferredHeight: 150
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: root.uiTheme.space3
                                spacing: root.uiTheme.space2
                                StatusBadge { theme: root.uiTheme; text: "CONTROLLED"; tone: "neutral" }
                                Label { text: "Locomotion experiments"; color: root.uiTheme.text; font.pixelSize: root.uiTheme.textTitle; font.weight: Font.DemiBold }
                                Label { text: "Single run · max-speed sweep · environment comparison."; color: root.uiTheme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                                Item { Layout.fillHeight: true }
                            }
                        }
                        SurfacePanel {
                            theme: root.uiTheme
                            Layout.fillWidth: true
                            Layout.preferredHeight: 150
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: root.uiTheme.space3
                                spacing: root.uiTheme.space2
                                StatusBadge { theme: root.uiTheme; text: "CUSTOM"; tone: "neutral" }
                                Label { text: "Reference Ecology"; color: root.uiTheme.text; font.pixelSize: root.uiTheme.textTitle; font.weight: Font.DemiBold }
                                Label { text: "Bounded Workbench-supported ecological composition."; color: root.uiTheme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                                Item { Layout.fillHeight: true }
                            }
                        }
                    }

                    DiagnosticBanner {
                        theme: root.uiTheme
                        tone: root.app.statusTone
                        title: "Application status"
                        message: root.app.status
                        visible: root.app.status.length > 0
                        Layout.fillWidth: true
                    }
                    Item { Layout.preferredHeight: root.uiTheme.space3 }
                }
            }

            Component.onCompleted: homeNewButton.forceActiveFocus(Qt.TabFocusReason)
        }
    }

    Component {
        id: newRoute
        FocusScope {
            id: newScope
            objectName: "newRoute"

            ScrollView {
                anchors.fill: parent
                contentWidth: availableWidth
                clip: true

                ColumnLayout {
                    width: Math.min(1180, Math.max(0, newScope.width - root.uiTheme.space5 * 2))
                    x: Math.max(root.uiTheme.space5, Math.round((newScope.width - width) / 2))
                    spacing: root.uiTheme.space4

                    Item { Layout.preferredHeight: root.uiTheme.space3 }
                    RowLayout {
                        Layout.fillWidth: true
                        WorkbenchButton {
                            id: newHomeButton
                            theme: root.uiTheme
                            text: "← Home"
                            onClicked: root.app.goHome()
                        }
                        Item { Layout.fillWidth: true }
                    }
                    SectionHeader {
                        theme: root.uiTheme
                        eyebrow: "New Study"
                        title: "Choose a supported scientific workflow"
                        description: "Each choice creates an existing concrete Workbench artifact. The desktop layer does not wrap them in a universal Study format."
                        Layout.fillWidth: true
                    }

                    Label { text: "CURATED"; color: root.uiTheme.subtleText; font.pixelSize: root.uiTheme.textSmall; font.weight: Font.DemiBold }
                    SurfacePanel {
                        theme: root.uiTheme
                        Layout.fillWidth: true
                        implicitHeight: b3NewContent.implicitHeight + root.uiTheme.space4 * 2
                        RowLayout {
                            id: b3NewContent
                            anchors.fill: parent
                            anchors.margins: root.uiTheme.space4
                            spacing: root.uiTheme.space3
                            ColumnLayout {
                                Layout.fillWidth: true
                                Label { text: "B3 Flagship"; color: root.uiTheme.text; font.pixelSize: root.uiTheme.textTitle; font.weight: Font.DemiBold }
                                Label { text: "Start from the canonical validated radius-1 B3 scientific definition."; color: root.uiTheme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                            }
                            WorkbenchButton {
                                id: b3StartButton
                                objectName: "newB3Study"
                                theme: root.uiTheme
                                primary: true
                                text: "Start"
                                onClicked: root.app.createStudy("b3-flagship")
                            }
                        }
                    }

                    Label { text: "CONTROLLED"; color: root.uiTheme.subtleText; font.pixelSize: root.uiTheme.textSmall; font.weight: Font.DemiBold }
                    GridLayout {
                        Layout.fillWidth: true
                        columns: newScope.width >= 1120 ? 3 : 1
                        columnSpacing: root.uiTheme.space3
                        rowSpacing: root.uiTheme.space3

                        SurfacePanel {
                            theme: root.uiTheme
                            Layout.fillWidth: true
                            implicitHeight: 170
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: root.uiTheme.space3
                                spacing: root.uiTheme.space2
                                Label { text: "Single controlled run"; color: root.uiTheme.text; font.pixelSize: 17; font.weight: Font.DemiBold }
                                Label { text: "One bounded controlled-locomotion Study revision."; color: root.uiTheme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                                Item { Layout.fillHeight: true }
                                WorkbenchButton { theme: root.uiTheme; text: "Start controlled run"; Layout.fillWidth: true; onClicked: root.app.createStudy("controlled-run") }
                            }
                        }
                        SurfacePanel {
                            theme: root.uiTheme
                            Layout.fillWidth: true
                            implicitHeight: 170
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: root.uiTheme.space3
                                spacing: root.uiTheme.space2
                                Label { text: "Max-speed sweep"; color: root.uiTheme.text; font.pixelSize: 17; font.weight: Font.DemiBold }
                                Label { text: "Existing E3-pattern maximum-speed factor sweep."; color: root.uiTheme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                                Item { Layout.fillHeight: true }
                                WorkbenchButton { theme: root.uiTheme; text: "Start max-speed sweep"; Layout.fillWidth: true; onClicked: root.app.createStudy("max-speed-sweep") }
                            }
                        }
                        SurfacePanel {
                            theme: root.uiTheme
                            Layout.fillWidth: true
                            implicitHeight: 170
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: root.uiTheme.space3
                                spacing: root.uiTheme.space2
                                Label { text: "Environment comparison"; color: root.uiTheme.text; font.pixelSize: 17; font.weight: Font.DemiBold }
                                Label { text: "Existing E4 matched environment-selection comparison."; color: root.uiTheme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                                Item { Layout.fillHeight: true }
                                WorkbenchButton { theme: root.uiTheme; text: "Start environment comparison"; Layout.fillWidth: true; onClicked: root.app.createStudy("environment-selection-comparison") }
                            }
                        }
                    }

                    Label { text: "CUSTOM"; color: root.uiTheme.subtleText; font.pixelSize: root.uiTheme.textSmall; font.weight: Font.DemiBold }
                    SurfacePanel {
                        theme: root.uiTheme
                        Layout.fillWidth: true
                        implicitHeight: referenceNewContent.implicitHeight + root.uiTheme.space4 * 2
                        RowLayout {
                            id: referenceNewContent
                            anchors.fill: parent
                            anchors.margins: root.uiTheme.space4
                            spacing: root.uiTheme.space3
                            ColumnLayout {
                                Layout.fillWidth: true
                                Label { text: "Reference Ecology"; color: root.uiTheme.text; font.pixelSize: root.uiTheme.textTitle; font.weight: Font.DemiBold }
                                Label { text: "Start the bounded WB4 recipe. Extension/internal engine capabilities remain outside ordinary authoring."; color: root.uiTheme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                            }
                            WorkbenchButton { theme: root.uiTheme; primary: true; text: "Start"; onClicked: root.app.createStudy("reference-ecology") }
                        }
                    }
                    Item { Layout.preferredHeight: root.uiTheme.space3 }
                }
            }

            Component.onCompleted: b3StartButton.forceActiveFocus(Qt.TabFocusReason)
        }
    }

    Component {
        id: openRoute
        FocusScope {
            id: openScope
            objectName: "openRoute"

            ColumnLayout {
                anchors.centerIn: parent
                width: Math.min(680, Math.max(0, parent.width - root.uiTheme.space5 * 2))
                spacing: root.uiTheme.space3

                WorkbenchButton { theme: root.uiTheme; text: "← Home"; onClicked: root.app.goHome() }
                SurfacePanel {
                    theme: root.uiTheme
                    Layout.fillWidth: true
                    implicitHeight: openContent.implicitHeight + root.uiTheme.space5 * 2
                    ColumnLayout {
                        id: openContent
                        anchors.fill: parent
                        anchors.margins: root.uiTheme.space5
                        spacing: root.uiTheme.space3
                        SectionHeader {
                            theme: root.uiTheme
                            eyebrow: "Open Study"
                            title: "Open an exact Workbench artifact"
                            description: "The native shell dispatches by existing format and pattern identity, then calls the concrete loader. Historical manifests are never re-resolved."
                            Layout.fillWidth: true
                        }
                        WorkbenchButton {
                            id: chooseOpenButton
                            objectName: "chooseOpenStudyFile"
                            theme: root.uiTheme
                            primary: true
                            text: "Choose JSON file…"
                            Layout.alignment: Qt.AlignLeft
                            onClicked: openDialog.open()
                        }
                    }
                }
                DiagnosticBanner {
                    theme: root.uiTheme
                    visible: root.app.diagnosticMessage.length > 0 || root.app.statusTone === "error"
                    tone: "error"
                    title: root.app.diagnosticMessage.length > 0 ? "Exact reproduction unavailable" : "Open failed"
                    message: root.app.diagnosticMessage.length > 0 ? root.app.diagnosticMessage : root.app.status
                    remediation: root.app.diagnosticRemediation
                    Layout.fillWidth: true
                }
            }

            Component.onCompleted: chooseOpenButton.forceActiveFocus(Qt.TabFocusReason)
        }
    }

    Component {
        id: studyRoute
        FocusScope {
            id: studyScope
            objectName: "studyRoute"

            RowLayout {
                anchors.fill: parent
                anchors.margins: root.uiTheme.space3
                spacing: root.uiTheme.space3

                SurfacePanel {
                    theme: root.uiTheme
                    Layout.preferredWidth: studyScope.width >= 1180 ? 218 : 188
                    Layout.minimumWidth: 178
                    Layout.maximumWidth: 218
                    Layout.fillHeight: true
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: root.uiTheme.space3
                        spacing: root.uiTheme.space2

                        WorkbenchButton {
                            id: studyHomeButton
                            theme: root.uiTheme
                            text: "← Home"
                            enabled: !root.app.running
                            Layout.fillWidth: true
                            onClicked: root.app.goHome()
                        }
                        Item { Layout.preferredHeight: root.uiTheme.space2 }
                        Label { text: "STUDY"; color: root.uiTheme.subtleText; font.pixelSize: root.uiTheme.textSmall; font.weight: Font.DemiBold; font.letterSpacing: 0.7 }
                        SidebarButton {
                            id: simulationNav
                            objectName: "sectionSimulation"
                            theme: root.uiTheme
                            text: "Simulation"
                            selected: root.app.studySection === "Simulation"
                            Layout.fillWidth: true
                            KeyNavigation.down: evidenceNav
                            onClicked: root.app.selectSection("Simulation")
                        }
                        SidebarButton {
                            id: evidenceNav
                            objectName: "sectionEvidence"
                            theme: root.uiTheme
                            text: "Evidence"
                            selected: root.app.studySection === "Evidence"
                            Layout.fillWidth: true
                            KeyNavigation.up: simulationNav
                            KeyNavigation.down: experimentNav
                            onClicked: root.app.selectSection("Evidence")
                        }
                        SidebarButton {
                            id: experimentNav
                            objectName: "sectionExperiment"
                            theme: root.uiTheme
                            text: "Experiment"
                            selected: root.app.studySection === "Experiment"
                            Layout.fillWidth: true
                            KeyNavigation.up: evidenceNav
                            KeyNavigation.down: resultsNav
                            onClicked: root.app.selectSection("Experiment")
                        }
                        SidebarButton {
                            id: resultsNav
                            objectName: "sectionResults"
                            theme: root.uiTheme
                            text: "Results"
                            selected: root.app.studySection === "Results"
                            Layout.fillWidth: true
                            KeyNavigation.up: experimentNav
                            KeyNavigation.down: presentationNav
                            onClicked: root.app.selectSection("Results")
                        }
                        SidebarButton {
                            id: presentationNav
                            objectName: "sectionPresentation"
                            theme: root.uiTheme
                            text: "Presentation"
                            selected: root.app.studySection === "Presentation"
                            Layout.fillWidth: true
                            KeyNavigation.up: resultsNav
                            onClicked: root.app.selectSection("Presentation")
                        }
                        Item { Layout.fillHeight: true }
                        Label {
                            text: root.app.fileLocation.length > 0 ? "Saved file\n" + root.app.fileLocation : "No file location yet"
                            color: root.uiTheme.subtleText
                            font.pixelSize: root.uiTheme.textSmall
                            wrapMode: Text.WrapAnywhere
                            Layout.fillWidth: true
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: root.uiTheme.space3

                    SurfacePanel {
                        theme: root.uiTheme
                        Layout.fillWidth: true
                        implicitHeight: studyHeaderContent.implicitHeight + root.uiTheme.space3 * 2
                        ColumnLayout {
                            id: studyHeaderContent
                            anchors.fill: parent
                            anchors.margins: root.uiTheme.space3
                            spacing: root.uiTheme.space2

                            Label {
                                text: root.app.studyTitle
                                color: root.uiTheme.text
                                font.pixelSize: root.uiTheme.textTitle
                                font.weight: Font.DemiBold
                                wrapMode: Text.Wrap
                                Layout.fillWidth: true
                            }
                            Label {
                                text: root.app.studyTypeLabel
                                color: root.uiTheme.mutedText
                                font.pixelSize: root.uiTheme.textSmall
                                wrapMode: Text.Wrap
                                Layout.fillWidth: true
                            }
                            Flow {
                                Layout.fillWidth: true
                                Layout.preferredHeight: childrenRect.height
                                spacing: root.uiTheme.space2
                                StatusBadge {
                                    theme: root.uiTheme
                                    visible: root.app.revisionId.length > 0
                                    text: "REV " + root.app.revisionId
                                    tone: "neutral"
                                }
                                StatusBadge {
                                    theme: root.uiTheme
                                    text: root.app.readinessState.toUpperCase()
                                    tone: root.app.readinessState === "ready" ? "success" : root.app.readinessState === "blocked" ? "error" : "warning"
                                }
                                StatusBadge {
                                    theme: root.uiTheme
                                    visible: root.app.scenarioIdentity.length > 0
                                    text: "VALIDATED SCENARIO"
                                    tone: "success"
                                }
                            }

                            GridLayout {
                                Layout.fillWidth: true
                                columns: studyScope.width >= 1220 ? 4 : 2
                                columnSpacing: root.uiTheme.space2
                                rowSpacing: root.uiTheme.space2
                                WorkbenchButton {
                                    theme: root.uiTheme
                                    text: "Fork"
                                    visible: root.app.canFork
                                    enabled: root.app.canFork && !root.app.running
                                    Layout.fillWidth: true
                                    onClicked: root.app.forkStudy()
                                }
                                WorkbenchButton {
                                    theme: root.uiTheme
                                    text: root.app.hasFileLocation ? "Save" : "Save As…"
                                    enabled: !root.app.running
                                    Layout.fillWidth: true
                                    onClicked: {
                                        if (root.app.hasFileLocation)
                                            root.app.saveToCurrentLocation()
                                        else
                                            saveDialog.open()
                                    }
                                }
                                WorkbenchButton {
                                    theme: root.uiTheme
                                    text: "Save As…"
                                    enabled: !root.app.running
                                    Layout.fillWidth: true
                                    onClicked: saveDialog.open()
                                }
                                WorkbenchButton {
                                    id: runStudyButton
                                    objectName: "runStudy"
                                    theme: root.uiTheme
                                    primary: true
                                    text: root.app.running ? "Running…" : "Run"
                                    enabled: root.app.canRun
                                    Layout.fillWidth: true
                                    onClicked: root.app.runStudy()
                                    ToolTip.visible: hovered && !enabled
                                    ToolTip.text: "Resolve any blocked scientific draft before opening the exact Run Plan."
                                }
                            }
                        }
                    }

                    DiagnosticBanner {
                        theme: root.uiTheme
                        visible: root.app.diagnosticMessage.length > 0
                        tone: "error"
                        title: "Exact reproduction unavailable"
                        message: root.app.diagnosticMessage
                        remediation: root.app.diagnosticRemediation
                        Layout.fillWidth: true
                    }

                    Loader {
                        id: sectionLoader
                        objectName: "sectionLoader"
                        enabled: !root.app.running
                        focus: true
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
                        onLoaded: Qt.callLater(function() {
                            if (item)
                                item.forceActiveFocus(Qt.TabFocusReason)
                        })
                    }

                    Label {
                        Layout.fillWidth: true
                        text: root.app.status
                        color: root.app.statusTone === "error"
                            ? root.uiTheme.danger
                            : root.app.statusTone === "warning"
                                ? root.uiTheme.warning
                                : root.app.statusTone === "success"
                                    ? root.uiTheme.success
                                    : root.uiTheme.mutedText
                        font.pixelSize: root.uiTheme.textSmall
                        wrapMode: Text.Wrap
                        Accessible.name: root.app.status
                        Accessible.role: Accessible.StaticText
                    }
                }
            }
        }
    }

    Component {
        id: simulationSection
        SimulationAuthoringView {
            theme: root.uiTheme
            app: root.app
            reference: root.reference
            simulation: root.simulation
        }
    }

    Component {
        id: evidenceSection
        EvidenceAuthoringView {
            theme: root.uiTheme
            app: root.app
            evidence: root.evidence
        }
    }

    Component {
        id: experimentSection
        ExperimentAuthoringView {
            theme: root.uiTheme
            app: root.app
            experiment: root.experiment
        }
    }

    Component {
        id: resultsSection
        ResultsView {
            theme: root.uiTheme
            app: root.app
            results: root.results
            reference: root.reference
        }
    }

    Component {
        id: presentationSection
        PresentationView {
            theme: root.uiTheme
            app: root.app
            presentation: root.presentation
        }
    }
}
