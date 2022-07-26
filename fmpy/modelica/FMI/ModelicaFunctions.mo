within FMI;
class ModelicaFunctions
  extends ExternalObject;

  impure function constructor
    output ModelicaFunctions functions;

    external "C" functions = ModelicaUtilityFunctions_getModelicaUtilityFunctions() annotation (
      Include = "#include \"ModelicaUtilityFunctions.c\"",
      IncludeDirectory="modelica://FMI/Resources/Include");
  end constructor;

  impure function destructor
    input ModelicaFunctions functions;
  external "C" ModelicaUtilityFunctions_freeModelicaUtilityFunctions(functions) annotation (
      Include = "#include \"ModelicaUtilityFunctions.c\"",
      IncludeDirectory="modelica://FMI/Resources/Include");
  end destructor;

  annotation(Icon(coordinateSystem(preserveAspectRatio=false, extent={{-100,-100},{100,100}}), graphics={
          Rectangle(
            lineColor={160,160,164},
            fillColor={160,160,164},
            fillPattern=FillPattern.Solid,
            extent={{-100.0,-100.0},{100.0,100.0}},
            radius=25.0)}));
end ModelicaFunctions;
