import { Endpoint, EndpointParameters as __EndpointParameters, EndpointV2, Provider } from "@smithy/types";
/**
 * @public
 */
export interface ClientInputEndpointParameters {
    region?: string | Provider<string>;
    useDualstackEndpoint?: boolean | Provider<boolean>;
    useFipsEndpoint?: boolean | Provider<boolean>;
    endpoint?: string | Provider<string> | Endpoint | Provider<Endpoint> | EndpointV2 | Provider<EndpointV2>;
    accountId?: string | Provider<string>;
    accountIdEndpointMode?: string | Provider<string>;
}
export type ClientResolvedEndpointParameters = ClientInputEndpointParameters & {
    defaultSigningName: string;
};
export declare const resolveClientEndpointParameters: <T>(options: T & ClientInputEndpointParameters) => T & ClientInputEndpointParameters & {
    defaultSigningName: string;
};
export declare const commonParams: {
    readonly UseFIPS: {
        readonly type: "builtInParams";
        readonly name: "useFipsEndpoint";
    };
    readonly AccountId: {
        readonly type: "builtInParams";
        readonly name: "accountId";
    };
    readonly Endpoint: {
        readonly type: "builtInParams";
        readonly name: "endpoint";
    };
    readonly Region: {
        readonly type: "builtInParams";
        readonly name: "region";
    };
    readonly UseDualStack: {
        readonly type: "builtInParams";
        readonly name: "useDualstackEndpoint";
    };
    readonly AccountIdEndpointMode: {
        readonly type: "builtInParams";
        readonly name: "accountIdEndpointMode";
    };
};
export interface EndpointParameters extends __EndpointParameters {
    Region?: string;
    UseDualStack?: boolean;
    UseFIPS?: boolean;
    Endpoint?: string;
    AccountId?: string;
    AccountIdEndpointMode?: string;
}
