import * as T from 'three';
import {DisplayManager} from "./DisplayManager";
import {Vector3} from "three";

/**
 * @class BaseModule
 * Template class for features.
 *
 */
export abstract class BaseModule extends T.EventDispatcher<any>{
    public readonly id: string;
    private _initialized = false;
    private _deps: Dependency[] = null;
    protected constructor(id: string) {
        super()
        this.id = id;
    }

    protected initDeps(deps: Dependency[], inherit: Boolean = true){
        if(this._deps == null || !inherit) this._deps = deps;
        else this._deps = this._deps.concat(deps)
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
    readonly pos: T.Vector3 = new T.Vector3();
    readonly rot: T.Vector3 = new T.Vector3();
    readonly events?: EventListenerBinding[]
}

export class EventListenerBinding{
    public type: string;
    public listener: T.EventListener<any, any, any>;
}

export class Dependency{
    readonly id: string;
    readonly type: InstanceType<any>;


    constructor(id: string, type: InstanceType<any>) {
        this.id = id;
        this.type = type;
    }
}