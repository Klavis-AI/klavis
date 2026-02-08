declare module "mongodb-redact" {
    function redact<T>(message: T): T;
    export default redact;
}
