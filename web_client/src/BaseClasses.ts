import * as T from 'three';
import {OBJLoader} from "three/examples/jsm/loaders/OBJLoader";
import {MTLLoader} from "three/examples/jsm/loaders/MTLLoader";
import {DisplayManager} from "./DisplayManager";
import {Vector3} from "three";

/**
 * @class BaseModule
 * Template class for features.
 *
 */
export abstract class BaseModule {
    public readonly id: string;
    private _initialized = false;
    protected _deps: Dependency[];
    protected constructor(id: string) {
        this.id = id;
    }

    get deps(){
        return this._deps;
    }

    get initialized(){
        return this._initialized;
    }

    public init(display: DisplayManager){
        this._initialized = true;
    }

    public abstract enable(): void;

    public abstract disable(): void;
}

export class MeshLoadData{
    readonly path: string;
    readonly pos: T.Vector3;
    readonly rot: T.Vector3;

    constructor(path: string, pos: Vector3, rot: Vector3) {
        this.path = path;
        this.pos = pos;
        this.rot = rot;
    }
}

export class Dependency{
    readonly id: string;
    readonly type: InstanceType<any>;


    constructor(id: string, type: InstanceType<any>) {
        this.id = id;
        this.type = type;
    }
}