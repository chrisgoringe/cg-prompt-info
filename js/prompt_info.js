import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";

function impose_min_width() {
    const sz = this.origComputeSize();
    if (sz[0]<250) sz[0]=250;
    return sz;
}

function displayMessage(message) {
	var w = this.widgets?.find((w) => w.name === "display_text_widget");
	if (w === undefined) {
		w = ComfyWidgets["STRING"](this, "display_text_widget", ["STRING", { multiline: true }], app).widget;
		w.inputEl.readOnly = true;
		w.inputEl.style.opacity = 0.6;
		w.inputEl.style.fontSize = "9pt";
	}
	w.value = message;
	this.onResize?.(this.size);
};

function handleThingChoice(selection, _, node) {
    node.widgets.forEach((w) => { if (w != this && w != this.parent && w.onRemove) { w.onRemove(); } } ) 
    node.widgets = [this.parent, this,]
    if (selection=="Select Value") { return; }
    const split = selection.split(' ');
    const value = node.message[node.chosen][`${split[0]}puts`][split[1]];
    displayMessage.apply(node, [value]);
}

function handleNodeChoice(selection, _, node) {
    node.widgets.forEach((w) => { if (w != this && w.onRemove) { w.onRemove(); } } ) 
    node.widgets = [this,];
    if (selection=="Select Node") { return; }
    const chosen = selection.split(' ')[0];
    node.chosen = chosen;
    const options = ["Select Value",];
    for (const [key, value] of Object.entries(node.message[chosen].inputs)) {
        options.push(`in ${key}`)
    }
    for (const [key, value] of Object.entries(node.message[chosen].outputs)) {
        options.push(`out ${key}`)
    }
    const w = ComfyWidgets["COMBO"](node, "  ", [options,]).widget;
    w.callback = handleThingChoice;
    w.parent = this;
}

function handleThingMessage(message) {
    if (!this.origComputeSize) {
        this.origComputeSize = this.computeSize;
        this.computeSize = impose_min_width;
    }
    this.message = message;
    if (this.widgets) { this.widgets.forEach((w) => { if (w.onRemove) { w.onRemove(); } } ) }
    this.widgets = [];
    const node_labels = ["Select Node",]
    for (const [key, value] of Object.entries(message)) {
        node_labels.push(`${key} (${value.type})`);
    }
    const w = ComfyWidgets["COMBO"](this, " ", [node_labels,]).widget;
    w.callback = handleNodeChoice;
}

app.registerExtension({
	name: "cg.info.textmessage",
    async setup() {
        function messageHandler(event) {
            const id = event.detail.id;
            const message = event.detail.message;
            const node = app.graph._nodes_by_id[id];
            if (node && node.handleThingMessage) node.handleThingMessage(message);
            else (console.log(`node ${id} couldn't handle a message`));
        }
        api.addEventListener("cg.prompt_info.textmessage", messageHandler);
        api.addEventListener("cg.prompt_info.thingmessage", messageHandler);
    },
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeType.comfyClass=="ExtractInfo" ) {
            nodeType.prototype.displayMessage = displayMessage;
        }
        if (nodeType.comfyClass=="HuntInfo") {
            nodeType.prototype.handleThingMessage = handleThingMessage;
        }
    }
})