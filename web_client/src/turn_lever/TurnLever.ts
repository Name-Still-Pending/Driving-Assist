import {Environment} from "../Environment";
import {DisplayManager} from "../DisplayManager";
import * as T from "three";


enum LeverState{
    Neutral = 0,
    Right = 1,
    Left = -1
}

export class TurnLever extends Environment{
    static EVENT_LEVER_STATE_CHANGED = "lever_state_changed";
    private _leverState: LeverState = LeverState.Neutral;
    private _leverMesh: T.Mesh = null;
    constructor() {
        super("TurnLever");

        this.meshList = [{
            path: "./src/turn_lever/turn_lever_004.obj",
            pos: new T.Vector3(0, 0, 2),
            rot: new T.Vector3(0, -Math.PI * 0.5, Math.PI * 0.6),
            events: [
                {type: DisplayManager.ACTION_RIGHT_CLICK, listener: (event) => {
                        this.onLeverRightClick();
                    }},
                {type: DisplayManager.ACTION_LEFT_CLICK, listener: (event) => {
                        this.onLeverLeftClick();
                }}
            ]
        }];
    }
    get leverState(): LeverState {
        return this._leverState;
    }

    set leverState(value: LeverState) {
        let diff = this._leverState - value;
        let leverMesh = this.objects[0].children[0] as T.Mesh;
        if(leverMesh != null) leverMesh.rotateX(diff * Math.PI / 12);
        this._leverState = value;
    }

    onLeverRightClick(){
        if(this._leverState == LeverState.Right) return;
        this.leverState += 1;
        this.dispatchEvent({type: TurnLever.EVENT_LEVER_STATE_CHANGED, message: this.leverState});
    }

    onLeverLeftClick(){
        if(this.leverState == LeverState.Left) return;
        this.leverState -= 1;
    }


    init(display: DisplayManager) {
        super.init(display);

        // this._leverMesh = this.objects[0].children[0] as T.Mesh;
    }
}