import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ScrollView {
    id: root
    required property var theme
    required property var run
    contentWidth: availableWidth
    focus: true

    function focusInitialControl() {
        cancelButton.forceActiveFocus(Qt.TabFocusReason)
    }

    ColumnLayout {
        width: root.availableWidth
        spacing: root.theme.space3

        SectionHeader {
            theme: root.theme
            eyebrow: "Run / Exact scientific owner"
            title: root.run.title
            description: "Review the exact saved revision or experiment definition that will be executed. Run Plan state is transient and never becomes scientific persistence."
            Layout.fillWidth: true
        }

        DiagnosticBanner {
            theme: root.theme
            visible: root.run.bindingNotice.length > 0
            tone: "success"
            title: "Scientific draft bound before Run"
            message: root.run.bindingNotice
            Layout.fillWidth: true
        }

        SurfacePanel {
            theme: root.theme
            Layout.fillWidth: true
            implicitHeight: summaryColumn.implicitHeight + root.theme.space4 * 2
            ColumnLayout {
                id: summaryColumn
                anchors.fill: parent
                anchors.margins: root.theme.space4
                spacing: root.theme.space2
                Label {
                    text: "Exact run definition"
                    color: root.theme.text
                    font.pixelSize: 17
                    font.weight: Font.DemiBold
                }
                Repeater {
                    model: root.run.summaryModel
                    delegate: RowLayout {
                        required property string label
                        required property string value
                        Layout.fillWidth: true
                        spacing: root.theme.space3
                        Label {
                            text: label
                            color: root.theme.mutedText
                            font.pixelSize: root.theme.textSmall
                            Layout.preferredWidth: 190
                            wrapMode: Text.Wrap
                        }
                        Label {
                            text: value
                            color: root.theme.text
                            font.pixelSize: root.theme.textSmall
                            wrapMode: Text.WrapAnywhere
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }

        SurfacePanel {
            theme: root.theme
            Layout.fillWidth: true
            implicitHeight: evidenceColumn.implicitHeight + root.theme.space4 * 2
            ColumnLayout {
                id: evidenceColumn
                anchors.fill: parent
                anchors.margins: root.theme.space4
                spacing: root.theme.space2
                Label {
                    text: "Recorded evidence"
                    color: root.theme.text
                    font.pixelSize: 17
                    font.weight: Font.DemiBold
                }
                Repeater {
                    model: root.run.evidenceModel
                    delegate: ColumnLayout {
                        required property string label
                        required property string value
                        Layout.fillWidth: true
                        spacing: root.theme.space1
                        Label { text: "✓ " + label; color: root.theme.text; font.weight: Font.DemiBold }
                        Label { text: value; color: root.theme.mutedText; wrapMode: Text.Wrap; Layout.fillWidth: true }
                    }
                }
            }
        }

        SurfacePanel {
            theme: root.theme
            visible: root.run.expandedRunCount > 0
            Layout.fillWidth: true
            implicitHeight: Math.min(430, runColumn.implicitHeight + root.theme.space4 * 2)
            ColumnLayout {
                id: runColumn
                anchors.fill: parent
                anchors.margins: root.theme.space4
                spacing: root.theme.space2
                Label {
                    text: "Authoritative expanded design"
                    color: root.theme.text
                    font.pixelSize: 17
                    font.weight: Font.DemiBold
                }
                Repeater {
                    model: root.run.runModel
                    delegate: Label {
                        required property string maximumSpeed
                        required property string seed
                        required property string roleName
                        required property string environment
                        required property string resourceGeography
                        required property string standingComposition
                        required property string founderOrder
                        Layout.fillWidth: true
                        color: root.theme.mutedText
                        wrapMode: Text.Wrap
                        text: maximumSpeed.length > 0
                            ? "Speed " + maximumSpeed + " · seed " + seed + " · " + resourceGeography
                            : roleName + " · seed " + seed + " · " + environment
                                + (standingComposition.length > 0 ? " · standing " + standingComposition : "")
                                + (founderOrder.length > 0 ? " · founder order " + founderOrder : "")
                    }
                }
            }
        }

        DiagnosticBanner {
            theme: root.theme
            visible: root.run.advisoryMessage.length > 0
            tone: "warning"
            title: "Scientific advisory"
            message: root.run.advisoryMessage
            Layout.fillWidth: true
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.bottomMargin: root.theme.space4
            Item { Layout.fillWidth: true }
            WorkbenchButton {
                id: cancelButton
                objectName: "runPlanCancel"
                theme: root.theme
                text: "Cancel"
                enabled: !root.run.running
                onClicked: root.run.cancelPlan()
            }
            WorkbenchButton {
                id: executeButton
                objectName: "runPlanExecute"
                theme: root.theme
                primary: true
                text: root.run.executeLabel
                enabled: !root.run.running
                onClicked: root.run.executePlan()
            }
        }
    }
}