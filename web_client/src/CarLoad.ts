import {Environment} from "./Environment";
import {DisplayManager} from "./DisplayManager";
import * as T from "three";



export class CarLoad extends Environment{
    private _carMesh: T.Mesh = null;
    constructor() {
        super("CarLoad");

        this.meshList = [{
            path: "./res/Caravan.obj",
            pos: new T.Vector3(0, -1.5, 0),
            rot: new T.Vector3(0, Math.PI, 0),
        },
        {
            path: "./res/Painel.obj",
            pos: new T.Vector3(0, -0.9, -0.9),
            rot: new T.Vector3(0, 0, 0),
        }];
    }

    // init(display: DisplayManager) {
    //     super.init(display);
    //
    //     // this._leverMesh = this.objects[0].children[0] as T.Mesh;
    // }
}