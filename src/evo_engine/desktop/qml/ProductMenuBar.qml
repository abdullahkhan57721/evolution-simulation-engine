import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

MenuBar {
    id: root

    required property var app
    required property var presentation

    Accessible.name: "Application menu"

    function presentationActive() {
        return root.app.route === "study"
            && root.app.studySection === "Presentation"
            && root.presentation.available
    }

    function navigateBack() {
        if (root.app.route === "new" || root.app.route === "open") {
            root.app.goHome()
            return
        }
        if (root.app.route !== "study")
            return
        var sections = ["Simulation", "Evidence", "Experiment", "Results", "Presentation"]
        var index = sections.indexOf(root.app.studySection)
        if (index > 0)
            root.app.selectSection(sections[index - 1])
    }

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
    Action {
        id: runAction
        text: root.app.running ? "Running…" : "Run…"
        shortcut: "Ctrl+R"
        enabled: root.app.canRun
        onTriggered: root.app.runStudy()
    }
    Action {
        id: homeAction
        text: "Return Home"
        shortcut: "Ctrl+Shift+H"
        enabled: root.app.route !== "home" && !root.app.running
        onTriggered: root.app.goHome()
    }
    Action {
        id: backAction
        text: "Back"
        shortcut: "Alt+Left"
        enabled: !root.app.running && (
            root.app.route === "new"
            || root.app.route === "open"
            || (root.app.route === "study" && root.app.studySection !== "Simulation")
        )
        onTriggered: root.navigateBack()
    }
    Action {
        id: focusAction
        text: root.presentation.focusMode ? "Exit Focus Mode" : "Focus Mode"
        shortcut: "Ctrl+Shift+F"
        enabled: root.presentationActive()
        onTriggered: root.presentation.toggleFocusMode()
    }
    Action {
        id: playAction
        text: root.presentation.playing ? "Pause Replay" : "Play Replay"
        shortcut: "Space"
        enabled: root.presentationActive() && root.presentation.stepCount > 1
        onTriggered: root.presentation.togglePlayback()
    }
    Action {
        id: previousAction
        text: "Previous Committed Step"
        shortcut: "Ctrl+Left"
        enabled: root.presentationActive() && root.presentation.canPrevious
        onTriggered: root.presentation.previousStep()
    }
    Action {
        id: nextAction
        text: "Next Committed Step"
        shortcut: "Ctrl+Right"
        enabled: root.presentationActive() && root.presentation.canNext
        onTriggered: root.presentation.nextStep()
    }

    Menu {
        title: "File"
        MenuItem { action: newAction }
        MenuItem { action: openAction }
        MenuSeparator {}
        MenuItem { action: saveAction }
        MenuItem { action: saveAsAction }
    }
    Menu {
        title: "Study"
        MenuItem { action: runAction }
        MenuSeparator {}
        MenuItem { action: backAction }
        MenuItem { action: homeAction }
    }
    Menu {
        title: "Presentation"
        MenuItem { action: focusAction }
        MenuSeparator {}
        MenuItem { action: previousAction }
        MenuItem { action: playAction }
        MenuItem { action: nextAction }
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
}
