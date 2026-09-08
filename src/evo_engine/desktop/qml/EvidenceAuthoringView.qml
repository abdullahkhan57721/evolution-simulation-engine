import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ScrollView {
    id: root
    property var theme
    property var app
    property var evidence
    contentWidth: availableWidth
    clip: true

    ColumnLayout {
        width: root.width
        spacing: theme.space3

        SectionHeader {
            theme: root.theme
            eyebrow: "Study / Evidence"
            title: "Evidence"
            description: "Choose concrete evidence streams before execution. Evidence controls what can later be inspected or analyzed; unrecorded evidence cannot be reconstructed."
            Layout.fillWidth: true
        }

        DiagnosticBanner {
            theme: root.theme
            visible: evidence.lockMessage.length > 0
            tone: "neutral"
            title: "Scientific design owns this evidence set"
            message: evidence.lockMessage
            Layout.fillWidth: true
        }

        Repeater {
            model: evidence.optionModel
            delegate: SurfacePanel {
                required property string evidenceId
                required property string label
                required property string meaning
                required property string enables
                required property bool selected
                required property bool required
                required property bool editable
                theme: root.theme
                Layout.fillWidth: true
                implicitHeight: optionContent.implicitHeight + theme.space3 * 2

                RowLayout {
                    id: optionContent
                    anchors.fill: parent
                    anchors.margins: theme.space3
                    spacing: theme.space3

                    CheckBox {
                        checked: selected
                        enabled: editable
                        onClicked: evidence.setEvidenceSelected(evidenceId, checked)
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: theme.space1
                        RowLayout {
                            Layout.fillWidth: true
                            Label { text: label; color: theme.text; font.weight: Font.DemiBold; Layout.fillWidth: true }
                            StatusBadge { theme: root.theme; visible: required; text: "REQUIRED"; tone: "neutral" }
                            StatusBadge { theme: root.theme; visible: !required && selected; text: "SELECTED"; tone: "success" }
                        }
                        Label { text: meaning; color: theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                        Label { text: "Enables: " + enables; color: theme.subtleText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                    }
                }
            }
        }

        DiagnosticBanner {
            theme: root.theme
            visible: evidence.advisoryMessage.length > 0
            tone: "warning"
            title: "Evidence advisory"
            message: evidence.advisoryMessage
            Layout.fillWidth: true
        }

        DiagnosticBanner {
            theme: root.theme
            visible: evidence.missingEvidenceMessage.length > 0
            tone: "neutral"
            title: "Unavailable after the run"
            message: evidence.missingEvidenceMessage
            Layout.fillWidth: true
        }

        SurfacePanel {
            theme: root.theme
            visible: evidence.editable
            Layout.fillWidth: true
            implicitHeight: evidenceActions.implicitHeight + theme.space4 * 2
            ColumnLayout {
                id: evidenceActions
                anchors.fill: parent
                anchors.margins: theme.space4
                spacing: theme.space2
                RowLayout {
                    Layout.fillWidth: true
                    StatusBadge { theme: root.theme; text: evidence.draftDirty ? "UNSAVED DRAFT" : "EXACT SAVED PLAN"; tone: evidence.draftDirty ? "warning" : "success" }
                    Label { text: evidence.readinessMessage; color: evidence.draftReady ? theme.mutedText : theme.warning; wrapMode: Text.Wrap; Layout.fillWidth: true }
                    WorkbenchButton {
                        theme: root.theme
                        text: "Save evidence child"
                        primary: true
                        enabled: evidence.draftDirty && evidence.draftReady && !app.running
                        onClicked: evidence.saveEvidenceChildRevision()
                    }
                }
            }
        }
    }
}
