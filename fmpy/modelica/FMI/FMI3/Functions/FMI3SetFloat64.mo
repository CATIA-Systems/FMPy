within FMI.FMI3.Functions;
impure function FMI3SetFloat64
  input Internal.ExternalFMU externalFMU;
    input Integer valueReferences[nValueReferences];
    input Integer nValueReferences;
    input Real values[nValueReferences];
    external"C" FMU_FMI3SetFloat64(externalFMU, valueReferences, nValueReferences, values) annotation (Library="ModelicaFMI");
end FMI3SetFloat64;
