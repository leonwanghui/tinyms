# Copyright 2021 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
import os
import json

import tinyms as ts
from tinyms.model import Model, lenet5, resnet50

servable_path = '/etc/tinyms/serving/servable.json'


def servable_search(name=None):
    # Check if servable_path existed
    if not os.path.exists(servable_path):
        err_msg = "Servable NOT found in "+servable_path
        return {"status": 1, "err_msg": err_msg}

    with open(servable_path, 'r') as f:
        servable_list = json.load(f)
    if name is not None:
        # check if servable name is valid
        def servable_exist(name):
            for servable in servable_list:
                if name in servable.values():
                    return servable
            return None
        servable = servable_exist(name)
        if servable is None:
            err_msg = "Servable name NOT supported!"
            return {"status": 1, "err_msg": err_msg}
        else:
            return {"status": 0, "servables": [servable]}
    else:
        return {"status": 0, "servables": servable_list}


def predict(instance, servable_name, servable_model):
    model_name = servable_model['name']
    model_format = servable_model['format']
    class_num = servable_model['class_num']
    # check if servable model name is valid
    if model_name not in ("lenet5", "resnet50"):
        err_msg = "Currently model_name only supports `lenet5` and `resnet50`!"
        return {"status": 1, "err_msg": err_msg}
    # check if model_format is valid
    if model_format not in ("ckpt"):
        err_msg = "Currently model_format only supports `ckpt`!"
        return {"status": 1, "err_msg": err_msg}

    # parse the input data
    input = ts.array(json.loads(instance['data']), dtype=ts.float32)
    input = ts.reshape(input, (1, 1, 28, 28)) if model_name == "lenet5" \
        else ts.reshape(input, (1, 3, 224, 224))
    # build the network
    net = lenet5(class_num=class_num) if model_name == "lenet5" else resnet50(class_num=class_num)
    model = Model(net)
    # load checkpoint
    ckpt_path = os.path.join("/etc/tinyms/serving", servable_name, model_name+"."+model_format)
    if not os.path.isfile(ckpt_path):
        err_msg = "The model path "+ckpt_path+" not exist!"
        return {"status": 1, "err_msg": err_msg}
    model.load_checkpoint(ckpt_path)
    # execute the network to perform model prediction
    data = model.predict(input).asnumpy()

    return {"status": 0, "instance": {"shape": data.shape, "data": json.dumps(data.tolist())}}
