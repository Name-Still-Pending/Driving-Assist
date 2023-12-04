import {BaseModule, MeshLoadData} from "./BaseClasses";
import {DisplayManager} from "./DisplayManager";
import * as T from 'three';

export class Environment extends BaseModule{
    private objects: T.Object3D[];
    protected readonly meshList: MeshLoadData[];

    constructor(name: string, loadData: MeshLoadData[]) {
        super("Environment_" + name);
        this.meshList = loadData;
        this.objects = new Array<T.Object3D>();
    }

    disable() {
        for (const mesh of this.objects) {
            mesh.visible = false;
        }
    }

    enable() {
        for (const mesh of this.objects) {
            mesh.visible = true;
        }
    }

    init(display: DisplayManager) {
        super.init(display)
        this.loadObjects(display, display.scene);
    }

    protected loadObjects(display: DisplayManager, parent?: T.Object3D){
        for (const data of this.meshList) {
            display.loadOBJ(data.path, data.pos, data.rot, parent, this.objects);
        }
    }

}