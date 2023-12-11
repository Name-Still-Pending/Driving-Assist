import {BaseModule} from "./BaseClasses";
import {DisplayManager} from "./DisplayManager";


export class Feature{
    readonly id: string;
    private connectFunction?: Function;
    modules: ModuleData<any>[];


    constructor(id: string, modules: ModuleData<any>[], connectFunction?: Function) {
        this.id = id;
        this.connectFunction = connectFunction;
        this.modules = modules;
    }

    init(display: DisplayManager){
        for (const module of this.modules) {
            module.init(display, this.id);
        }
        if(this.connectFunction !== undefined) this.connectFunction();
    }
}

export class ModuleData<T>{
    private module: new (...Params: any[]) => BaseModule;
    private params?: any[];
    private instance: BaseModule;


    constructor(module: new (...Params: any[]) => BaseModule, params?: any[]) {
        this.module = module;
        this.params = params;
    }

    init(display: DisplayManager, featureId: string){
        this.instance = this.params === undefined ? new this.module() : new this.module(...this.params);
        if(display.modules[this.instance.id] != undefined) {
            this.instance = display.modules[this.instance.id];
        }
        else display.addModule(this.instance);
        this.instance.users.push(featureId);
    }
}