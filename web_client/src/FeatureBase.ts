import * as thr from 'three';
import {OBJLoader} from "three/examples/jsm/loaders/OBJLoader";

/**
 * @class FeatureBase
 * Template class for features
 */
abstract class FeatureBase{
    _id: string;
    _models: thr.Mesh[];
    _threads: Array<Promise<any>>;
    constructor(id: string){
        this._id = id;
        this._models = new Array<thr.Mesh>();
        this._threads = new Array<Promise<any>>;
    }

    getId() : string{
        return this._id;
    }

    addMesh(path : string, pos: Number[], rot: Number[]){

    }

    enable(){}
    disable(){}

}