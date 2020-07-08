"""
A script to refine a given Zinc mesh and export it to Zinc and VTK file formats.
Requires: OpenCMISS-ZINC, OpenCMISS.utils, ScaffoldMaker.
"""

import os
import argparse

from opencmiss.zinc.context import Context as ZincContext
from opencmiss.utils.zinc.field import get_group_list

from scaffoldmaker.utils.meshrefinement import MeshRefinement
from scaffoldmaker.annotation.annotationgroup import AnnotationGroup
from scaffoldmaker.utils.exportvtk import ExportVtk


class ProgramArguments(object):
    pass


class RefineAndExport:

    def __init__(self, input_zinc_file, input_exelem_file=None, refine=None, output_zinc_file=None, output_vtk_file=None):
        self._context = ZincContext("RefineContext")
        self._region = self._context.getDefaultRegion()
        self._input_zinc_file = input_zinc_file
        self._region.readFile(self._input_zinc_file)
        if input_exelem_file is not None:
            self._region.readFile(input_exelem_file)
        self._field_module = self._region.getFieldmodule()
        self._annotation_groups = [AnnotationGroup(self._region,
                                                   (group.getName(), None)) for group in get_group_list(self._field_module)]
        self._field_module.defineAllFaces()
        for group in self._annotation_groups:
            group.addSubelements()

        """ Refine """
        self._refine_factor = refine
        self._refined_region, self._refined_annotation_groups = self._refine()

        """ Export to Zinc file"""
        self._refined_region.writeFile(output_zinc_file)

        """ Export to VTK """
        description = "Stomach Scaffold"
        exportvtk = ExportVtk(self._refined_region, description, self._refined_annotation_groups)
        exportvtk.writeFile(output_vtk_file)

    def _refine(self):
        target_region = self._region.createChild('RefinedRegion')
        mesh_refinement = MeshRefinement(self._region, target_region, self._annotation_groups)
        mesh = self._get_mesh()
        element_iterator = mesh.createElementiterator()
        element = element_iterator.next()
        while element.isValid():
            number_in_xi1 = self._refine_factor[0]
            if len(self._refine_factor) > 1:
                number_in_xi2 = self._refine_factor[1]
            else:
                number_in_xi2 = 1
            if len(self._refine_factor) > 2:
                number_in_xi3 = self._refine_factor[2]
            else:
                number_in_xi3 = 1
            mesh_refinement.refineElementCubeStandard3d(element, number_in_xi1, number_in_xi2, number_in_xi3)
            element = element_iterator.next()
        return target_region, mesh_refinement.getAnnotationGroups()

    def _get_mesh(self):
        for dimension in range(3, 0, -1):
            mesh = self._field_module.findMeshByDimension(dimension)
            if mesh.getSize() > 0:
                return mesh
        raise ValueError('Model contains no mesh')


def main():
    args = parse_args()
    if os.path.exists(args.input_ex):
        if args.output_ex is None:
            filename = os.path.basename(args.input_ex)
            dirname = os.path.dirname(args.input_ex)
            output_ex = os.path.join(dirname, filename.split('.')[0] + '_refined.' + filename.split('.')[1])
        else:
            output_ex = args.output_ex

        if args.output_vtk is None:
            filename = os.path.basename(args.input_ex)
            dirname = os.path.dirname(args.input_ex)
            output_vtk = os.path.join(dirname, filename.split('.')[0] + '_refined.vtk')
        else:
            output_vtk = args.output_vtk

        if args.exelem is not None:
            exelem_file = args.exelem

        if args.refine_factor is None:
            refine_factor = [4, 4, 1]
        else:
            refine_factor = [int(i) for i in list(args.refine_factor)]

        RefineAndExport(args.input_ex,
                        input_exelem_file=None,
                        refine=refine_factor,
                        output_zinc_file=output_ex,
                        output_vtk_file=output_vtk)


def parse_args():
    parser = argparse.ArgumentParser(description="Refine and export a given ZINC model scaffold.")
    parser.add_argument("input_ex", help="Location of the input EX file.")
    parser.add_argument("-exelem", "--exelem", help="Optional - Location of the exelem file.")
    parser.add_argument("-r", "--refine_factor", help="Refine factor for each xi coordinate direction."
                                                      "[default is '4,4,1'.")
    parser.add_argument("-oe", "--output_ex", help="Location of the output Zinc file."
                                                   "[defaults to the location of the input file if not set.]")
    parser.add_argument("-ov", "--output_vtk", help="Location of the output vtk file. "
                                                    "[defaults to the location of the input file if not set.]")

    program_arguments = ProgramArguments()
    parser.parse_args(namespace=program_arguments)

    return program_arguments


if __name__ == "__main__":
    main()
