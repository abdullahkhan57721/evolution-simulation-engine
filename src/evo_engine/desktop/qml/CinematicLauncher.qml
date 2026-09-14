import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    required property var app
    required property var cinematic

    implicitWidth: storyButton.implicitWidth
    implicitHeight: storyButton.implicitHeight

    WorkbenchButton {
        id: storyButton
        objectName: "b3ScientificStoryButton"
        theme: root.theme
        primary: root.cinematic.storyAvailable
        text: root.cinematic.rendering ? "Rendering B3 Story…" : "B3 Scientific Story"
        enabled: !root.cinematic.rendering
        Accessible.name: "B3 Scientific Story"
        Accessible.description: root.cinematic.message
        onClicked: storyPopup.open()
    }

    Popup {
        id: storyPopup
        parent: Overlay.overlay
        modal: true
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        width: Math.min(520, parent ? parent.width - root.theme.space4 * 2 : 520)
        height: contentColumn.implicitHeight + root.theme.space4 * 2
        x: parent ? Math.round((parent.width - width) / 2) : 0
        y: parent ? Math.round((parent.height - height) / 2) : 0

        background: Rectangle {
            color: root.theme.canvasRaised
            radius: root.theme.radius
            border.color: root.theme.border
        }

        contentItem: ColumnLayout {
            id: contentColumn
            spacing: root.theme.space3

            SectionHeader {
                theme: root.theme
                eyebrow: "B3 / Presentation"
                title: "Validated scientific story"
                description: "Scientific eligibility, representative evidence, and bounded conclusion come from the existing B3 Workbench handoff. Render quality and file format are presentation-only."
                Layout.fillWidth: true
            }

            DiagnosticBanner {
                theme: root.theme
                tone: root.cinematic.storyAvailable ? "success" : "warning"
                title: root.cinematic.storyAvailable
                    ? "Scientific story available"
                    : "Scientific story unavailable"
                message: root.cinematic.message
                Layout.fillWidth: true
            }

            Label {
                visible: root.cinematic.storyAvailable && !root.cinematic.rendererAvailable
                text: "The current runtime does not include the optional Manim renderer. The scientific handoff remains valid and the native interactive world remains available."
                color: root.theme.mutedText
                font.pixelSize: root.theme.textSmall
                wrapMode: Text.Wrap
                Layout.fillWidth: true
                Accessible.role: Accessible.StaticText
            }

            RowLayout {
                visible: root.cinematic.storyAvailable && root.cinematic.rendererAvailable
                Layout.fillWidth: true
                spacing: root.theme.space3

                ColumnLayout {
                    Layout.fillWidth: true
                    Label {
                        text: "Render quality"
                        color: root.theme.subtleText
                        font.pixelSize: root.theme.textSmall
                    }
                    ComboBox {
                        id: qualityChoice
                        objectName: "b3CinematicQuality"
                        model: ["Low", "Medium", "High"]
                        currentIndex: 1
                        activeFocusOnTab: true
                        Accessible.name: "B3 cinematic render quality"
                        Layout.fillWidth: true
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Label {
                        text: "Output"
                        color: root.theme.subtleText
                        font.pixelSize: root.theme.textSmall
                    }
                    ComboBox {
                        id: outputChoice
                        objectName: "b3CinematicOutputFormat"
                        model: ["MP4", "GIF"]
                        activeFocusOnTab: true
                        Accessible.name: "B3 cinematic output format"
                        Layout.fillWidth: true
                    }
                }
            }

            ProgressBar {
                visible: root.cinematic.rendering
                indeterminate: true
                Layout.fillWidth: true
                Accessible.name: "B3 cinematic rendering"
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: root.theme.space2

                WorkbenchButton {
                    theme: root.theme
                    primary: true
                    text: root.cinematic.rendering ? "Rendering…" : "Render to File…"
                    enabled: root.cinematic.storyAvailable
                        && root.cinematic.rendererAvailable
                        && !root.cinematic.rendering
                    onClicked: renderDialog.open()
                }
                WorkbenchButton {
                    theme: root.theme
                    text: "Open Rendered File"
                    visible: root.cinematic.hasOutput
                    enabled: root.cinematic.hasOutput
                    onClicked: root.cinematic.openOutput()
                }
                Item { Layout.fillWidth: true }
                WorkbenchButton {
                    theme: root.theme
                    text: "Close"
                    onClicked: storyPopup.close()
                }
            }

            Label {
                visible: root.cinematic.hasOutput
                text: root.cinematic.outputPath
                color: root.theme.subtleText
                font.pixelSize: root.theme.textSmall
                elide: Text.ElideMiddle
                Layout.fillWidth: true
                Accessible.name: "Rendered B3 story file " + root.cinematic.outputPath
            }
        }

        onOpened: Qt.callLater(function() {
            qualityChoice.forceActiveFocus(Qt.TabFocusReason)
        })
    }

    FileDialog {
        id: renderDialog
        title: "Render B3 Scientific Story"
        fileMode: FileDialog.SaveFile
        defaultSuffix: outputChoice.currentText === "GIF" ? "gif" : "mp4"
        nameFilters: outputChoice.currentText === "GIF"
            ? ["Animated GIF (*.gif)"]
            : ["MPEG-4 video (*.mp4)"]
        onAccepted: root.cinematic.renderStory(
            selectedFile.toString(),
            qualityChoice.currentText.toLowerCase()
        )
    }
}
