import QtQuick

WorkbenchShell {
    id: shell

    menuBar: ProductMenuBar {
        app: applicationController
        presentation: presentationController
    }

    CinematicLauncher {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: shell.uiTheme.space4
        anchors.bottomMargin: shell.uiTheme.space4
        z: 100
        theme: shell.uiTheme
        app: applicationController
        cinematic: cinematicController
        visible: applicationController.route === "study"
            && applicationController.studySection === "Presentation"
            && applicationController.artifactKind === "b3-flagship"
    }
}
