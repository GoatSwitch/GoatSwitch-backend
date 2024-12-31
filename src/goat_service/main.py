from dapr.ext.grpc import App, InvokeMethodRequest
from gs_common import setup_logging, timed
from gs_common.dev import daprcache
from gs_common.proto.tl_generator_pb2 import PlanGeneratorResponse, TLGeneratorResponse
from gs_common.proto.tl_generator_pb2 import ReturnCode as TLGeneratorReturnCode
from gs_common.proto.tl_picker_pb2 import TLPickerResponse
from gs_common.proto.ut_generator_pb2 import ReturnCode as UTGeneratorReturnCode
from gs_common.proto.ut_generator_pb2 import UTGeneratorResponse
from gs_common.proto.ut_picker_pb2 import UTPickerResponse

from src.goat_service.tl_generator.tl_gen_service import TLGenService
from src.goat_service.tl_picker.tl_picker_service import TLPickerService
from src.goat_service.ut_generator.ut_gen_service import UTGenService
from src.goat_service.ut_picker.ut_picker_service import UTPickerService

setup_logging("goat_service")
app = App(max_grpc_message_length=128 * 1024 * 1024)

FAILED_MSG = "Unknown error occurred. Please try again or contact support at hello@goatswitch.ai."


@app.method(name="assess")
@timed()
def assess(request: InvokeMethodRequest) -> TLGeneratorResponse:
    return tl_gen_service.assess(request)


@app.method(name="generate_plan")
@timed()
def generate_plan(request: InvokeMethodRequest) -> PlanGeneratorResponse:
    resp = tl_gen_service.generate_plan(request)
    if resp.return_code == TLGeneratorReturnCode.FAILED:
        raise TimeoutError(FAILED_MSG)
    return resp


@app.method(name="generate_unittests")
# @daprcache(3)
@timed()
def generate_unittests(request: InvokeMethodRequest) -> UTGeneratorResponse:
    resp = ut_gen_service.generate_unittests(request)
    if resp.return_code == UTGeneratorReturnCode.FAILED:
        raise TimeoutError(FAILED_MSG)
    return resp


@app.method(name="pick_unittests")
@timed()
def pick_unittests(request: InvokeMethodRequest) -> UTPickerResponse:
    return ut_picker_service.pick_unittests(request)


@app.method(name="generate_translations")
# @daprcache(3)
@timed()
def generate_translations(request: InvokeMethodRequest) -> TLGeneratorResponse:
    resp = tl_gen_service.generate_translations(request)
    if resp.return_code == TLGeneratorReturnCode.FAILED:
        raise TimeoutError(FAILED_MSG)
    return resp


@app.method(name="pick_translation")
@timed()
def pick_translation(request: InvokeMethodRequest) -> TLPickerResponse:
    return tl_picker_service.pick_translation(request)


if __name__ == "__main__":
    tl_gen_service = TLGenService()
    tl_picker_service = TLPickerService()
    ut_gen_service = UTGenService()
    ut_picker_service = UTPickerService()
    app.run(4999)
