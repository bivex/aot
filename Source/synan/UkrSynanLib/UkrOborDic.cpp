#include "UkrOborDic.h"
#include "UkrSyntaxOpt.h"

CUkrOborDic::CUkrOborDic(const CSyntaxOpt* Opt) : COborDic(Opt)
{
    // Common Ukrainian conjunctions
    m_SimpleCoordConj.push_back({"І", false});
    m_SimpleCoordConj.push_back({"ТА", false});
    m_SimpleCoordConj.push_back({"А", false});
    m_SimpleCoordConj.push_back({"АЛЕ", false});
    m_SimpleCoordConj.push_back({"АБО", false});
    m_SimpleCoordConj.push_back({"ЧИ", false});

    m_SimpleSubConj.push_back("ЩО");
    m_SimpleSubConj.push_back("БО");
    m_SimpleSubConj.push_back("ТОМУ");
    m_SimpleSubConj.push_back("ЯКЩО");
    m_SimpleSubConj.push_back("КОЛИ");
    m_SimpleSubConj.push_back("ХОЧ");
    m_SimpleSubConj.push_back("ЯК");
}
