from pathlib import Path
import argparse

import yaml

file_dir = Path(__file__).parent.absolute()
proj_root = file_dir.parent.parent.parent


cs_pattern = """using MCServerLauncher.Daemon.Storage;
using MCServerLauncher.Daemon.Minecraft.Server;
using MCServerLauncher.Daemon.Minecraft.Server.Factory;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace {namespace};

/// <summary>
/// Action的消息模版,采用meta-program
/// Generated by "{meta_path}"
/// </summary>
public static class {class_name}
{
    private static readonly JsonSerializer Serializer = JsonSerializer.Create(WebJsonConverter.Settings);

    private static T Deserialize<T>(JObject? data) =>
        data!.ToObject<T>(Serializer) ?? throw new ArgumentException("Action request deserialize failed.");


    public interface IActionResponse
    {
        public JObject Into(JsonSerializer serializer)
        {
            return JObject.FromObject(this, serializer);
        }
    }

    public static class Empty
    {
        public struct Request {}

        private struct Response : IActionResponse {}

        public static Request RequestOf()
        {
            return new Request();
        }

        public static IActionResponse ResponseOf()
        {
            return new Response();
        }
    }
{classes}
}
"""

class_pattern = """
        public static class {class_name}
        {
            public struct Request
            {
{req_fields}
            }

            private struct Response : IActionResponse
            {
{resp_fields}
            }

            public static {request} RequestOf(JObject? data)
            {
                return {request_ret};
            }

            public static IActionResponse ResponseOf({func_args})
            {
                return new Response { {struct_decl} };
            }
        }
"""

empty_request_class_pattern = """            public class Request
            {

            }

"""

field_pattern = """                public {T} {field_name};"""

func_arg_pattern = """{T} {field_name}"""
struct_decl_pattern = """{field_name} = {arg_name}"""

action_type_pattern = """namespace {namespace};
public enum ActionType
{
{action_types}
}"""


def snake2camel(name:str,big = True):
    # big camel
    if big:
        return ''.join([x.capitalize() for x in name.split('_')])

    # small camel
    groups = name.split('_')
    if len(groups) == 1:
        return groups[0]

    return groups[0] + ''.join([x.capitalize() for x in groups[1:]])

def yml2cs(actions:list[dict[str,dict[str,str]]], namespace:str, outer_class_name:str):
    _ = snake2camel

    cs = cs_pattern

    classes = []

    for action in actions:
        class_name, class_data = list(action.items())[0]

        request_fields = []
        # request fields
        request = class_data['req'] or []
        for field in request:
            request_fields.append(field_pattern.replace('{T}',request[field]).replace('{field_name}',_(field)))
        request_fields_str = '\n'.join(request_fields)


        response_fields = []
        # response fields
        response = class_data['resp'] or []
        for field in response:
            response_fields.append(field_pattern.replace('{T}',response[field]).replace('{field_name}',_(field)))
        response_fields_str = '\n'.join(response_fields)

        func_args = []
        struct_decls = []
        for field in response:
            func_args.append(func_arg_pattern.replace('{T}',response[field]).replace('{field_name}',_(field,False)))
            struct_decls.append(struct_decl_pattern.replace('{field_name}',_(field)).replace('{arg_name}',_(field, False)))
        func_args_str = ', '.join(func_args)
        struct_decls_str = ', '.join(struct_decls)

        # classes += class_pattern.replace('{class_name}',_(class_name)).replace('{req_fields}',request_fields).replace('{resp_fields}',response_fields)
        class_pattern_str = class_pattern\
            .replace('{class_name}',_(class_name))\
            .replace('{req_fields}',request_fields_str)\
            .replace('{resp_fields}',response_fields_str)\
            .replace('{func_args}',func_args_str)\
            .replace('{struct_decl}',struct_decls_str)\
            .replace('{request}','Empty.Request' if not request_fields else 'Request')\
            .replace('{request_ret}','new Empty.Request()' if not request_fields else 'Deserialize<Request>(data)')\
            .replace(empty_request_class_pattern,'') # delete empty request class
        classes.append(class_pattern_str)
    
    classes_str = ''.join(classes)
    return cs.replace('{namespace}',namespace).replace('{class_name}',_(outer_class_name)).replace('{classes}',classes_str)

def yml2enum(actions:list[dict[str,dict[str,str]]], namespace:str):
    _ = snake2camel

    action_types = []

    for action in actions:
        class_name = list(action.keys())[0]
        action_types.append(f"    {_(class_name)}")

    action_types_str = ',\n'.join(action_types)

    return action_type_pattern.replace('{namespace}',namespace).replace('{action_types}',action_types_str)



def main():
    parser = argparse.ArgumentParser(description='Generate Action source code from meta file')
    parser.add_argument('--meta', type=str,required=False ,help='Path to meta file')
    parser.add_argument('--out', type=str,required=True ,help='Path to output file (relative to project root)')

    args = parser.parse_args()
    meta_path = Path(args.meta or file_dir / 'actions_meta.yml')
    out_path = Path(args.out)

    namespace = out_path.parent.as_posix().replace('/','.')
    filename = out_path.stem

    actions = yaml.load(meta_path.read_text(), Loader=yaml.FullLoader)
    # import json
    # print(json.dumps(actions,indent=4,sort_keys=True))
    source = yml2cs(actions["actions"],namespace,filename).replace("{meta_path}",meta_path.relative_to(proj_root).as_posix())
    print(source)
    r = input(f"\n### Write to {out_path.as_posix()} (y/n)\n")
    if r.lower() == 'y':
        p = proj_root.joinpath(out_path)
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(source,encoding='utf-8')

    enum_source = yml2enum(actions["actions"],namespace)
    print(enum_source)
    out_path_enum = out_path.parent / "ActionType.cs"
    r = input(f"\n### Write to {out_path_enum.as_posix()} (y/n)\n")
    if r.lower() == 'y':
        p = proj_root.joinpath(out_path_enum)
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(enum_source,encoding='utf-8')


if __name__ == '__main__':
    main()