class TempStorage {
    protected store: any;
    public constructor() {
        this.store = {};
    }

    public set(key: string, value: any) {
        this.store[key] = value;
    }

    public get(key: string) {
        return this.store[key];
    }
}

export const tempStorage = new TempStorage();
