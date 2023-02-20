within FMI.FMI3.Functions;
impure function FMI3SetString
  input Internal.ExternalFMU externalFMU;
    input Integer valueReferences[nValueReferences];
    input Integer nValueReferences;
    input String values[nValueReferences];
    external"C" FMU_FMI3SetString(externalFMU, valueReferences, nValueReferences, values) annotation (Library="ModelicaFMI");
end FMI3SetString;
