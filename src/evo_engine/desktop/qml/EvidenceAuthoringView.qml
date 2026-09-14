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
        spacing: root.theme.space3

        SectionHeader {
            theme: root.theme
            eyebrow: "Study / Evidence"
            title: "Evidence"
            description: "Choose concrete evidence streams before execution. Evidence controls what can later be inspected or analyzed; unrecorded evidence cannot be reconstructed."
            Layout.fillWidth: true
        }

        DiagnosticBanner {
            theme: root.theme
            visible: root.evidence.lockMessage.length > 0
            tone: "neutral"
            title: "Scientific design owns this evidence set"
            message: root.evidence.lockMessage
            Layout.fillWidth: true
        }

        Repeater {
            model: root.evidence.optionModel
            delegate: SurfacePanel {
                id: optionPanel
                required property string evidenceId
                required property string label
                required property string meaning
                required property string enables
                required property bool selected
                required property bool required
                required property bool editable
                theme: root.theme
                Layout.fillWidth: true
                implicitHeight: optionContent.implicitHeight + root.theme.space3 * 2

                RowLayout {
                    id: optionContent
                    anchors.fill: parent
                    anchors.margins: root.theme.space3
                    spacing: root.theme.space3

                    CheckBox {
                        checked: optionPanel.selected
                        enabled: optionPanel.editable
                        activeFocusOnTab: true
                        Accessible.name: optionPanel.label
                        Accessible.description: optionPanel.meaning + ". Enables: " + optionPanel.enables
                        onClicked: root.evidence.setEvidenceSelected(optionPanel.evidenceId, checked)
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: root.theme.space1
                        RowLayout {
                            Layout.fillWidth: true
                            Label { text: optionPanel.label; color: root.theme.text; font.weight: Font.DemiBold; Layout.fillWidth: true }
                            StatusBadge { theme: root.theme; visible: optionPanel.required; text: "REQUIRED"; tone: "neutral" }
                            StatusBadge { theme: root.theme; visible: !optionPanel.required && optionPanel.selected; text: "SELECTED"; tone: "success" }
                        }
                        Label { text: optionPanel.meaning; color: root.theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                        Label { text: "Enables: " + optionPanel.enables; color: root.theme.subtleText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                    }
                }
            }
        }

        DiagnosticBanner {
            theme: root.theme
            visible: root.evidence.advisoryMessage.length > 0
            tone: "warning"
            title: "Evidence advisory"
            message: root.evidence.advisoryMessage
            Layout.fillWidth: true
        }

        DiagnosticBanner {
            theme: root.theme
            visible: root.evidence.missingEvidenceMessage.length > 0
            tone: "neutral"
            title: "Unavailable after the run"
            message: root.evidence.missingEvidenceMessage
            Layout.fillWidth: true
        }

        SurfacePanel {
            theme: root.theme
            visible: root.evidence.editable
            Layout.fillWidth: true
            implicitHeight: evidenceActions.implicitHeight + root.theme.space4 * 2
            ColumnLayout {
                id: evidenceActions
                anchors.fill: parent
                anchors.margins: root.theme.space4
                spacing: root.theme.space2
                RowLayout {
                    Layout.fillWidth: true
                    StatusBadge { theme: root.theme; text: root.evidence.draftDirty ? "UNSAVED DRAFT" : "EXACT SAVED PLAN"; tone: root.evidence.draftDirty ? "warning" : "success" }
                    Label { text: root.evidence.readinessMessage; color: root.evidence.draftReady ? root.theme.mutedText : root.theme.warning; wrapMode: Text.Wrap; Layout.fillWidth: true }
                    WorkbenchButton {
                        theme: root.theme
                        text: "Save evidence child"
                        primary: true
                        enabled: root.evidence.draftDirty && root.evidence.draftReady && !root.app.running
                        onClicked: root.evidence.saveEvidenceChildRevision()
                    }
                }
            }
        }
    }
}
