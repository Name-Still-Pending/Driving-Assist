import * as T from 'three'
import {BaseModule} from "./BaseClasses";
import {MTLLoader} from "three/examples/jsm/loaders/MTLLoader";
import {OBJLoader} from "three/examples/jsm/loaders/OBJLoader";
import {Scene} from "three";

export class DisplayManager{
    get modules(): {} {
        return this._modules;
    }
    private _camera: T.Camera
    private _scene: T.Scene
    private renderer: T.WebGLRenderer
    private domElement: HTMLElement


    private _modules: {};
    constructor(elementId: string) {
        this.domElement = document.getElementById(elementId);
        if(this.domElement == null){
            console.error("Element with ID " + elementId + " does not exist.");
            return;
        }
        if(!(this.domElement instanceof HTMLDivElement)){
            console.error(elementId + " is not a div.");
            return;
        }
        this.renderer = new T.WebGLRenderer();
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = T.PCFSoftShadowMap;
        this.renderer.setSize(this.domElement.clientWidth, this.domElement.clientHeight);
        this.domElement.appendChild(this.renderer.domElement);

        this._scene = new T.Scene();
        this._camera = new T.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);

        this._modules = {};
    }

    update(){
        this.renderer.render(this._scene, this._camera);
    }

    get camera(): T.Camera {
        return this._camera;
    }

    get scene(): Scene {
        return this._scene;
    }

    addModule(module: BaseModule, init = false, force = false){
        if(!force){
            for (const key in this._modules) {
                if(key == module.id){
                    console.error("Failed to load object: " + module.id + " already exists.");
                    return;
                }
            }
        }
        this._modules[module.id] = module;
        if (init) module.init(this);
    }

    loadOBJ(path: string, pos: T.Vector3, rot: T.Vector3, parent: T.Object3D = this._scene, objArray: T.Object3D[]): void {
        let lastDot = path.lastIndexOf('.');
        if (lastDot > 0) path = path.substring(0, lastDot);

        const mtlPath = path + ".mtl";
        const objPath = path + ".obj";

        new MTLLoader()
            .load(mtlPath,
                (materials) => {
                    materials.preload();
                    new OBJLoader()
                        .setMaterials(materials)
                        .load(objPath,
                            (object) => {
                                object.traverse((child) => {
                                    if(child instanceof T.Mesh){
                                        console.log("Loaded mesh: " + child.name);
                                    }
                                });
                                object.position.copy(pos);
                                object.rotateX(rot.x);
                                object.rotateY(rot.y);
                                object.rotateZ(rot.z);
                                object.receiveShadow = true;
                                object.castShadow = true;
                                object.updateMatrix();

                                parent.add(object);
                                objArray.push(object);
                            },
                            function ( xhr ) {
                                console.log( ( xhr.loaded / xhr.total * 100 ) + '% loaded' );
                            },
                            // called when loading has errors
                            function ( error ) {
                                console.log( 'An error happened: ' + error );
                            }
                        );
                })
    }

    initAll(){
        for (const key in this._modules) {
            let module = this._modules[key];
            if (!module.initialized) module.init(this);
        }
    }
}
