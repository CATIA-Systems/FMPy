within FMI.FMI3.Functions;
impure function FMI3SetInt32
  input Internal.ExternalFMU externalFMU;
    input Integer valueReferences[nValueReferences];
    input Integer nValueReferences;
    input Integer values[nValueReferences];
    external"C" FMU_FMI3SetInt32(externalFMU, valueReferences, nValueReferences, values) annotation (Library="ModelicaFMI");
end FMI3SetInt32;
