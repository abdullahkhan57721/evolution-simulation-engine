import QtQuick

WorkbenchShell {
    id: root

    WorkbenchTheme { id: q4Theme }

    Rectangle {
        id: presentationSurface
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: 250
        anchors.rightMargin: q4Theme.space3
        color: q4Theme.canvas
        visible: applicationController.route === "study"
            && applicationController.studySection === "Presentation"
        z: 1000

        PresentationView {
            anchors.fill: parent
            theme: q4Theme
            app: applicationController
            presentation: presentationController
        }
    }
}
