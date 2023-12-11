import * as T from 'three';
import {DisplayManager} from "./DisplayManager";
import {Vector3} from "three";
import {Feature} from "./Feature";

/**
 * @class BaseModule
 * Template class for features.
 *
 */
export abstract class BaseModule extends T.EventDispatcher<any>{
    public readonly id: string;
    private _initialized = false;
    public users: string[];
    protected constructor(id: string) {
        super()
        this.id = id;
        this.users = new Array<string>();
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

